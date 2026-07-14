import logging
from collections.abc import Callable, Iterator, Mapping, Sequence
from types import SimpleNamespace
from typing import cast
from unittest.mock import PropertyMock, patch

import pytest
from requests.exceptions import ReadTimeout, RequestException

from shopify_sdk.gql.core.bulk import (
    BulkResultDownloadError,
    BulkResultParseError,
)
from shopify_sdk.gql.core.bulk.download import (
    BulkDownloadRetryEvent,
    BulkResultDownloader,
    BulkResultDownloadResponse,
    BulkResultDownloadRetryPolicy,
)
from shopify_sdk.gql.core.bulk.poll import BulkActionResultManager
from shopify_sdk.gql.core.bulk.upload import JSONUploadManager


SIGNED_URL = "https://storage.example.test/results.jsonl?X-Amz-Signature=secret-signature"


class FakeDownloadResponse:
    def __init__(
        self,
        items: list[str | RequestException],
        *,
        status_code: int = 200,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        """Store one scripted streamed result-file response."""
        self._items = items
        self.status_code = status_code
        self.headers = dict(headers or {})
        self.closed = False

    def iter_lines(self, *, decode_unicode: bool) -> Iterator[str]:
        """Yield scripted lines or raise a transient Requests exception."""
        assert decode_unicode is True
        for item in self._items:
            if isinstance(item, RequestException):
                raise item
            yield item

    def close(self) -> None:
        """Record response resource cleanup."""
        self.closed = True


class FakeDownloadTransport:
    def __init__(
        self,
        responses: Sequence[FakeDownloadResponse | RequestException],
    ) -> None:
        """Store scripted download outcomes and capture signed URL requests safely."""
        self._responses = list(responses)
        self.urls: list[str] = []

    def get(
        self,
        url: str,
        *,
        stream: bool,
        timeout: float,
    ) -> BulkResultDownloadResponse:
        """Return the next scripted response without invoking a real network client."""
        assert stream is True
        assert timeout == 30
        self.urls.append(url)
        response = self._responses.pop(0)
        if isinstance(response, RequestException):
            raise response
        return cast(BulkResultDownloadResponse, response)


class FakeRuntime:
    def __init__(self) -> None:
        """Initialize deterministic delay recording for retry tests."""
        self.sleeps: list[float] = []
        self.on_sleep: Callable[[], None] | None = None

    def sleep(self, delay_seconds: float) -> None:
        """Record an attempted retry delay without waiting."""
        if self.on_sleep is not None:
            self.on_sleep()
        self.sleeps.append(delay_seconds)

    @staticmethod
    def random() -> float:
        """Return midpoint jitter so retry delays remain deterministic."""
        return 0.5


def downloader(
    transport: FakeDownloadTransport,
    runtime: FakeRuntime,
    events: list[BulkDownloadRetryEvent] | None = None,
) -> BulkResultDownloader:
    """Build a deterministic bulk downloader with the documented starting policy."""
    return BulkResultDownloader(
        transport=transport,
        policy=BulkResultDownloadRetryPolicy(jitter_ratio=0),
        sleep=runtime.sleep,
        random_value=runtime.random,
        on_retry=events.append if events is not None else None,
    )


def test_download_honors_retry_after_and_emits_safe_retry_event() -> None:
    """Retry a transient result-download response without exposing its signed URL."""
    runtime = FakeRuntime()
    events: list[BulkDownloadRetryEvent] = []
    first_response = FakeDownloadResponse(
        [],
        status_code=429,
        headers={"Retry-After": "2"},
    )
    second_response = FakeDownloadResponse(['{"id":"one"}'])
    transport = FakeDownloadTransport([first_response, second_response])
    runtime.on_sleep = lambda: assert_response_closed(first_response)

    lines = list(
        downloader(transport, runtime, events).iter_lines(
            results_url=SIGNED_URL,
            operation_id="gid://shopify/BulkOperation/1",
            timeout_s=30,
        )
    )

    assert lines == [(1, '{"id":"one"}')]
    assert runtime.sleeps == [2.0]
    assert events == [
        BulkDownloadRetryEvent(
            operation_id="gid://shopify/BulkOperation/1",
            failed_attempt=1,
            delay_seconds=2.0,
            reason="retry_after",
            status_code=429,
        )
    ]
    assert first_response.closed is True
    assert second_response.closed is True


def assert_response_closed(response: FakeDownloadResponse) -> None:
    """Assert a failed response has been closed before the downloader waits to retry."""
    assert response.closed is True


def test_download_replays_failed_stream_without_duplicate_lines() -> None:
    """Resume a failed stream by replaying and skipping already yielded physical lines."""
    runtime = FakeRuntime()
    first_response = FakeDownloadResponse(
        ['{"id":"one"}', ReadTimeout("connection interrupted")]
    )
    second_response = FakeDownloadResponse(['{"id":"one"}', '{"id":"two"}'])
    transport = FakeDownloadTransport([first_response, second_response])

    lines = list(
        downloader(transport, runtime).iter_lines(
            results_url=SIGNED_URL,
            operation_id="gid://shopify/BulkOperation/1",
            timeout_s=30,
        )
    )

    assert lines == [(1, '{"id":"one"}'), (2, '{"id":"two"}')]
    assert runtime.sleeps == [1.0]
    assert first_response.closed is True
    assert second_response.closed is True


def test_download_failure_redacts_signed_url_after_retry_limit() -> None:
    """Raise only safe operation/status metadata after bounded download retries."""
    runtime = FakeRuntime()
    responses = [FakeDownloadResponse([], status_code=503) for _ in range(3)]
    transport = FakeDownloadTransport(responses)

    with pytest.raises(BulkResultDownloadError) as captured_error:
        list(
            downloader(transport, runtime).iter_lines(
                results_url=SIGNED_URL,
                operation_id="gid://shopify/BulkOperation/1",
                timeout_s=30,
            )
        )

    assert captured_error.value.status_code == 503
    assert captured_error.value.attempts == 3
    assert SIGNED_URL not in str(captured_error.value)
    assert "secret-signature" not in str(captured_error.value)
    assert runtime.sleeps == [1.0, 2.0]


def test_parse_failure_redacts_signed_url_and_result_contents() -> None:
    """Expose only operation and line metadata for malformed JSONL records."""
    runtime = FakeRuntime()
    sensitive_line = '{"email":"secret@example.com"'
    transport = FakeDownloadTransport([FakeDownloadResponse([sensitive_line])])
    manager = BulkActionResultManager(
        "gid://shopify/BulkOperation/1",
        downloader=downloader(transport, runtime),
    )

    with pytest.raises(BulkResultParseError) as captured_error:
        list(manager._iter_result_lines(results_url=SIGNED_URL, timeout_s=30))

    assert captured_error.value.line_number == 1
    assert SIGNED_URL not in str(captured_error.value)
    assert "secret@example.com" not in str(captured_error.value)


def test_staged_upload_log_redacts_presigned_url(caplog: pytest.LogCaptureFixture) -> None:
    """Avoid logging the Requests exception string that can contain a signed upload URL."""
    manager = JSONUploadManager(content=b"{}\n", filename="bulk.jsonl")
    target = SimpleNamespace(url=SIGNED_URL, parameters=[])

    with (
        patch.object(
            JSONUploadManager,
            "target",
            new_callable=PropertyMock,
            return_value=target,
        ),
        patch(
            "shopify_sdk.gql.core.bulk.upload.requests.post",
            side_effect=RequestException(SIGNED_URL),
        ),
        caplog.at_level(logging.ERROR),
    ):
        assert manager.upload() is False

    assert SIGNED_URL not in caplog.text
    assert "secret-signature" not in caplog.text
