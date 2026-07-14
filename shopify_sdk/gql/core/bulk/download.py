"""Safe retrying transport for streaming Shopify bulk result files."""

import random
import time
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from math import isfinite
from typing import Protocol, cast

import requests
from pydantic import BaseModel, ConfigDict, Field, model_validator
from requests.exceptions import RequestException

from .models import BulkResultDownloadError


class BulkResultDownloadResponse(Protocol):
    """Describe the minimal streamed HTTP response needed for bulk result downloads."""

    status_code: int
    headers: Mapping[str, str]

    def iter_lines(self, *, decode_unicode: bool) -> Iterator[str]:
        """Yield result-file lines as decoded text."""

    def close(self) -> None:
        """Release the underlying HTTP response resources."""


class BulkResultDownloadTransport(Protocol):
    """Describe the narrow HTTP dependency used to fetch signed result files."""

    def get(
        self,
        url: str,
        *,
        stream: bool,
        timeout: float,
    ) -> BulkResultDownloadResponse:
        """Fetch one bulk result-file response."""


class BulkResultLineDownloader(Protocol):
    """Describe the replay-safe line stream consumed by bulk result parsing."""

    def iter_lines(
        self,
        *,
        results_url: str,
        operation_id: str,
        timeout_s: float,
        start_line_number: int = 1,
    ) -> Iterator[tuple[int, str]]:
        """Yield unacknowledged physical JSONL lines from a bulk result file."""


class RequestsBulkResultDownloadTransport:
    """Requests-backed adapter for signed Shopify bulk result-file downloads."""

    def get(
        self,
        url: str,
        *,
        stream: bool,
        timeout: float,
    ) -> BulkResultDownloadResponse:
        """Fetch a streamed signed result URL through Requests."""
        return cast(
            BulkResultDownloadResponse,
            requests.get(url, stream=stream, timeout=timeout),
        )


class BulkResultDownloadRetryPolicy(BaseModel):
    """Starting retry defaults for idempotent bulk result-file downloads."""

    max_attempts: int = Field(default=3, ge=1)
    initial_delay_seconds: float = Field(default=1.0, gt=0)
    maximum_delay_seconds: float = Field(default=8.0, gt=0)
    multiplier: float = Field(default=2.0, ge=1)
    jitter_ratio: float = Field(default=0.2, ge=0, le=1)
    retryable_status_codes: tuple[int, ...] = (429, 500, 502, 503, 504)
    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def validate_delay_bounds(self) -> "BulkResultDownloadRetryPolicy":
        """Ensure the maximum delay can accommodate the starting delay."""
        if self.maximum_delay_seconds < self.initial_delay_seconds:
            raise ValueError(
                "maximum_delay_seconds must be at least initial_delay_seconds."
            )
        return self


@dataclass(frozen=True)
class BulkDownloadRetryEvent:
    """Safe metadata emitted whenever a bulk result-file download is retried."""

    operation_id: str
    failed_attempt: int
    delay_seconds: float
    reason: str
    status_code: int | None = None


class BulkResultDownloader:
    """Stream a signed bulk result file with bounded retries and replay-safe progress."""

    def __init__(
        self,
        transport: BulkResultDownloadTransport | None = None,
        policy: BulkResultDownloadRetryPolicy | None = None,
        *,
        sleep: Callable[[float], None] = time.sleep,
        random_value: Callable[[], float] = random.random,
        on_retry: Callable[[BulkDownloadRetryEvent], None] | None = None,
    ) -> None:
        """Initialize injected transport, timing collaborators, and retry policy."""
        self._transport = transport or RequestsBulkResultDownloadTransport()
        self._policy = policy or BulkResultDownloadRetryPolicy()
        self._sleep = sleep
        self._random_value = random_value
        self._on_retry = on_retry

    def iter_lines(
        self,
        *,
        results_url: str,
        operation_id: str,
        timeout_s: float,
        start_line_number: int = 1,
    ) -> Iterator[tuple[int, str]]:
        """Yield unacknowledged physical JSONL lines while safely replaying failed streams."""
        if start_line_number < 1:
            raise ValueError("start_line_number must be at least one.")
        next_line_number = start_line_number
        failed_attempt = 0
        while True:
            response: BulkResultDownloadResponse | None = None
            try:
                response = self._transport.get(
                    results_url,
                    stream=True,
                    timeout=timeout_s,
                )
                if not self._is_success(response.status_code):
                    failed_attempt += 1
                    retry_event = self._http_retry_event(
                        response=response,
                        operation_id=operation_id,
                        failed_attempt=failed_attempt,
                    )
                    if retry_event is not None:
                        response.close()
                        response = None
                        self._emit_retry(retry_event)
                        continue
                    raise BulkResultDownloadError(
                        operation_id=operation_id,
                        attempts=failed_attempt,
                        status_code=response.status_code,
                    )
                for line_number, line in enumerate(
                    response.iter_lines(decode_unicode=True),
                    start=1,
                ):
                    if line_number < next_line_number:
                        continue
                    if not line:
                        next_line_number = line_number + 1
                        continue
                    yield line_number, line
                    next_line_number = line_number + 1
                return
            except RequestException:
                failed_attempt += 1
                retry_event = self._network_retry_event(operation_id, failed_attempt)
                if retry_event is not None:
                    if response is not None:
                        response.close()
                        response = None
                    self._emit_retry(retry_event)
                    continue
                raise BulkResultDownloadError(
                    operation_id=operation_id,
                    attempts=failed_attempt,
                ) from None
            finally:
                if response is not None:
                    response.close()

    def _http_retry_event(
        self,
        *,
        response: BulkResultDownloadResponse,
        operation_id: str,
        failed_attempt: int,
    ) -> BulkDownloadRetryEvent | None:
        """Return a retry event for a transient HTTP response when policy permits it."""
        if response.status_code not in self._policy.retryable_status_codes:
            return None
        if failed_attempt >= self._policy.max_attempts:
            return None
        delay_seconds = self._retry_after(response.headers)
        reason = "retry_after" if delay_seconds is not None else f"http_{response.status_code}"
        return BulkDownloadRetryEvent(
            operation_id=operation_id,
            failed_attempt=failed_attempt,
            delay_seconds=delay_seconds or self._backoff_delay(failed_attempt),
            reason=reason,
            status_code=response.status_code,
        )

    def _network_retry_event(
        self,
        operation_id: str,
        failed_attempt: int,
    ) -> BulkDownloadRetryEvent | None:
        """Return a retry event for a network error when policy permits another attempt."""
        if failed_attempt >= self._policy.max_attempts:
            return None
        return BulkDownloadRetryEvent(
            operation_id=operation_id,
            failed_attempt=failed_attempt,
            delay_seconds=self._backoff_delay(failed_attempt),
            reason="network",
            status_code=None,
        )

    def _emit_retry(
        self,
        event: BulkDownloadRetryEvent,
    ) -> None:
        """Emit safe retry telemetry and wait after closing a failed response."""
        if self._on_retry is not None:
            self._on_retry(event)
        self._sleep(event.delay_seconds)

    def _backoff_delay(self, failed_attempt: int) -> float:
        """Calculate a bounded jittered exponential retry delay."""
        unjittered_delay = min(
            self._policy.maximum_delay_seconds,
            self._policy.initial_delay_seconds
            * self._policy.multiplier ** (failed_attempt - 1),
        )
        if self._policy.jitter_ratio == 0:
            return unjittered_delay
        random_value = min(max(self._random_value(), 0.0), 1.0)
        jitter = (random_value * 2 - 1) * self._policy.jitter_ratio
        return unjittered_delay * (1 + jitter)

    @staticmethod
    def _retry_after(headers: Mapping[str, str]) -> float | None:
        """Return a valid numeric Retry-After value without retaining response content."""
        value = next(
            (
                header_value
                for header_name, header_value in headers.items()
                if header_name.casefold() == "retry-after"
            ),
            None,
        )
        if value is None:
            return None
        try:
            delay_seconds = float(value)
        except ValueError:
            return None
        if not isfinite(delay_seconds) or delay_seconds < 0:
            return None
        return delay_seconds

    @staticmethod
    def _is_success(status_code: int) -> bool:
        """Return whether an HTTP status code indicates a successful result response."""
        return 200 <= status_code < 300
