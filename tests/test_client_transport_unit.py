from __future__ import annotations

from collections.abc import Mapping
from typing import cast

import pytest
from pydantic import BaseModel
from requests.exceptions import ConnectTimeout
from requests.exceptions import ReadTimeout

from shopify_sdk.gql.core.client import ShopifyGraphQLError
from shopify_sdk.gql.core.client import GQLResponse
from shopify_sdk.gql.core.client import ShopifyHttpError
from shopify_sdk.gql.core.client import ShopifyNetworkError
from shopify_sdk.gql.core.client import ShopifyResponseDecodeError
from shopify_sdk.gql.core.client import ShopifyResponseValidationError
from shopify_sdk.gql.core.client import ShopifyTransportError
from shopify_sdk.gql.core.client import client_context
from shopify_sdk.gql.core.client.root import RootClient
from shopify_sdk.gql.core.client.retry import RequestRetryMode
from shopify_sdk.gql.core.client.retry import ShopifyRetryPolicy
from shopify_sdk.gql.core.client.transport import ShopifyHttpResponse
from shopify_sdk.gql.core.client.wrapper import ShopifyClientWrapper
from shopify_sdk.gql.core.mutation import Mutation
from shopify_sdk.gql.core.query import Query


class FakeResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        headers: Mapping[str, str] | None = None,
        payload: object | None = None,
        json_error: ValueError | None = None,
        text: str = "",
    ) -> None:
        self.status_code = status_code
        self.headers = dict(headers or {})
        self._payload = {} if payload is None else payload
        self._json_error = json_error
        self.text = text

    def json(self) -> Mapping[str, object]:
        if self._json_error is not None:
            raise self._json_error
        return cast(Mapping[str, object], self._payload)


class FakeTransport:
    def __init__(self, responses: list[FakeResponse | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def post(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        json: Mapping[str, object],
        timeout: tuple[float, float],
    ) -> ShopifyHttpResponse:
        self.calls.append(
            {
                "url": url,
                "headers": dict(headers),
                "json": dict(json),
                "timeout": timeout,
            }
        )
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return cast(ShopifyHttpResponse, response)


class FakeRuntime:
    def __init__(self) -> None:
        """Initialize a deterministic monotonic clock and recorded sleep calls."""
        self.current_time = 0.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        """Return the current deterministic monotonic time."""
        return self.current_time

    def sleep(self, delay_seconds: float) -> None:
        """Record a requested delay and advance deterministic time."""
        self.sleeps.append(delay_seconds)
        self.current_time += delay_seconds

    @staticmethod
    def random() -> float:
        """Return midpoint jitter so tests receive the nominal retry delay."""
        return 0.5


class ProbePayload(BaseModel):
    """Minimal payload used to test query and mutation retry mode propagation."""

    ok: bool


class ReadProbe(Query):
    """Minimal read operation for retry mode propagation tests."""

    return_type = ProbePayload


class MutationProbe(Mutation):
    """Minimal mutation operation for retry mode propagation tests."""

    return_type = ProbePayload


class RetryModeRecordingClient:
    def __init__(self) -> None:
        """Initialize captured retry modes from executed SDK operations."""
        self.retry_modes: list[RequestRetryMode] = []

    def request(
        self,
        query: str,
        variables: dict[str, object],
        *,
        retry_mode: RequestRetryMode = RequestRetryMode.NEVER,
    ) -> GQLResponse:
        """Capture retry mode and return successful payloads for both probes."""
        self.retry_modes.append(retry_mode)
        return GQLResponse(
            data={
                "ReadProbe": {"ok": True},
                "MutationProbe": {"ok": True},
            }
        )


def _client(
    transport: FakeTransport,
    *,
    retry_policy: ShopifyRetryPolicy | None = None,
    runtime: FakeRuntime | None = None,
) -> RootClient:
    active_runtime = runtime or FakeRuntime()
    return RootClient(
        shop_domain="example.myshopify.com",
        access_token="token",
        api_version="2026-07",
        transport=transport,
        retry_policy=retry_policy,
        sleep=active_runtime.sleep,
        monotonic_clock=active_runtime.monotonic,
        random_value=active_runtime.random,
    )


def _success_response(data: Mapping[str, object] | None = None) -> FakeResponse:
    return FakeResponse(payload={"data": dict(data or {})})


def test_request_uses_injected_transport_and_parses_success_response() -> None:
    transport = FakeTransport([_success_response({"shop": {"id": "shop-1"}})])

    response = _client(transport).request("query Shop { shop { id } }")

    assert response.data == {"shop": {"id": "shop-1"}}
    assert transport.calls == [
        {
            "url": "https://example.myshopify.com/admin/api/2026-07/graphql.json",
            "headers": {
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": "token",
            },
            "json": {"query": "query Shop { shop { id } }", "variables": {}},
            "timeout": (10.0, 30.0),
        }
    ]


@pytest.mark.parametrize("exception", [ConnectTimeout("connect"), ReadTimeout("read")])
def test_request_maps_network_failures_to_transport_errors(exception: Exception) -> None:
    with pytest.raises(ShopifyTransportError) as exc_info:
        _client(FakeTransport([exception])).request("query { shop { id } }")

    assert exc_info.value.status_code is None
    assert "connect" not in str(exc_info.value)
    assert "read" not in str(exc_info.value)


def test_request_exposes_429_metadata_without_response_body() -> None:
    response = FakeResponse(
        status_code=429,
        headers={
            "x-request-id": "request-1",
            "retry-after": "2",
            "content-type": "application/json",
        },
        text='{"sensitive":"customer@example.com"}',
    )

    with pytest.raises(ShopifyHttpError) as exc_info:
        _client(FakeTransport([response])).request("query { shop { id } }")

    error = exc_info.value
    assert error.status_code == 429
    assert error.request_id == "request-1"
    assert error.retry_after == "2"
    assert "customer@example.com" not in str(error)


def test_safe_read_retries_429_after_retry_after_delay() -> None:
    """Retry a safe read after Shopify's explicit numeric Retry-After delay."""
    runtime = FakeRuntime()
    transport = FakeTransport(
        [
            FakeResponse(status_code=429, headers={"Retry-After": "2"}),
            _success_response({"shop": {"id": "shop-1"}}),
        ]
    )

    response = _client(transport, runtime=runtime).request(
        "query { shop { id } }",
        retry_mode=RequestRetryMode.SAFE_READ,
    )

    assert response.data == {"shop": {"id": "shop-1"}}
    assert len(transport.calls) == 2
    assert runtime.sleeps == [2.0]


def test_safe_read_uses_backoff_when_retry_after_is_invalid() -> None:
    """Fall back to the Shopify-recommended one-second delay for invalid headers."""
    runtime = FakeRuntime()
    transport = FakeTransport(
        [
            FakeResponse(status_code=429, headers={"Retry-After": "tomorrow"}),
            _success_response({"shop": {"id": "shop-1"}}),
        ]
    )

    _client(transport, runtime=runtime).request(
        "query { shop { id } }",
        retry_mode=RequestRetryMode.SAFE_READ,
    )

    assert runtime.sleeps == [1.0]


def test_safe_read_retries_network_timeout_with_documented_one_second_backoff() -> None:
    """Retry a network timeout after Shopify's recommended one-second backoff."""
    runtime = FakeRuntime()
    transport = FakeTransport(
        [
            ConnectTimeout("connect"),
            _success_response({"shop": {"id": "shop-1"}}),
        ]
    )

    response = _client(transport, runtime=runtime).request(
        "query { shop { id } }",
        retry_mode=RequestRetryMode.SAFE_READ,
    )

    assert response.data == {"shop": {"id": "shop-1"}}
    assert len(transport.calls) == 2
    assert runtime.sleeps == [1.0]


def test_direct_request_does_not_retry_even_for_retryable_statuses() -> None:
    """Keep direct client requests conservative unless a caller opts into safe reads."""
    runtime = FakeRuntime()
    transport = FakeTransport(
        [
            FakeResponse(status_code=503),
            _success_response({"shop": {"id": "shop-1"}}),
        ]
    )

    with pytest.raises(ShopifyHttpError):
        _client(transport, runtime=runtime).request("query { shop { id } }")

    assert len(transport.calls) == 1
    assert runtime.sleeps == []


def test_safe_read_stops_after_configured_retry_attempts() -> None:
    """Preserve the final structured failure after bounded safe-read retries."""
    runtime = FakeRuntime()
    transport = FakeTransport(
        [
            FakeResponse(status_code=503),
            FakeResponse(status_code=503),
            FakeResponse(status_code=503),
        ]
    )
    policy = ShopifyRetryPolicy(jitter_ratio=0)

    with pytest.raises(ShopifyHttpError) as captured_error:
        _client(transport, retry_policy=policy, runtime=runtime).request(
            "query { shop { id } }",
            retry_mode=RequestRetryMode.SAFE_READ,
        )

    assert captured_error.value.status_code == 503
    assert len(transport.calls) == 3
    assert runtime.sleeps == [1.0, 2.0]


def test_safe_read_uses_graphql_cost_to_delay_throttled_retry() -> None:
    """Use Shopify throttle cost metadata when it exceeds exponential backoff."""
    runtime = FakeRuntime()
    throttled_payload = {
        "errors": [{"extensions": {"code": "THROTTLED"}}],
        "extensions": {
            "cost": {
                "requestedQueryCost": 100,
                "throttleStatus": {
                    "maximumAvailable": 100,
                    "currentlyAvailable": 0,
                    "restoreRate": 50,
                },
            }
        },
    }
    transport = FakeTransport(
        [
            FakeResponse(payload=throttled_payload),
            _success_response({"shop": {"id": "shop-1"}}),
        ]
    )

    response = _client(transport, runtime=runtime).request(
        "query { shop { id } }",
        retry_mode=RequestRetryMode.SAFE_READ,
    )

    assert response.data == {"shop": {"id": "shop-1"}}
    assert len(transport.calls) == 2
    assert runtime.sleeps == [2.0]


def test_network_failures_are_distinct_from_non_retryable_transport_failures() -> None:
    """Expose the retryable network subtype without exposing provider error content."""
    with pytest.raises(ShopifyNetworkError):
        _client(FakeTransport([ConnectTimeout("connect")])).request(
            "query { shop { id } }"
        )


def test_query_and_mutation_execution_use_different_retry_modes() -> None:
    """Allow automatic retries only for SDK query execution paths."""
    client = RetryModeRecordingClient()

    ReadProbe().execute(cast(ShopifyClientWrapper, client))
    MutationProbe().execute(cast(ShopifyClientWrapper, client))

    assert client.retry_modes == [
        RequestRetryMode.SAFE_READ,
        RequestRetryMode.NEVER,
    ]


@pytest.mark.parametrize("status_code", [500, 503])
def test_request_maps_server_errors(status_code: int) -> None:
    with pytest.raises(ShopifyHttpError) as exc_info:
        _client(
            FakeTransport([FakeResponse(status_code=status_code)])
        ).request("query { shop { id } }")

    assert exc_info.value.status_code == status_code


def test_request_rejects_malformed_success_json_without_body_leakage() -> None:
    response = FakeResponse(
        headers={"content-type": "application/json"},
        json_error=ValueError("invalid JSON"),
        text="customer@example.com",
    )

    with pytest.raises(ShopifyResponseDecodeError) as exc_info:
        _client(FakeTransport([response])).request("query { shop { id } }")

    assert exc_info.value.content_type == "application/json"
    assert "customer@example.com" not in str(exc_info.value)


def test_request_preserves_top_level_graphql_errors() -> None:
    graphql_errors = [{"message": "Access denied", "path": ["shop"]}]

    with pytest.raises(ShopifyGraphQLError) as exc_info:
        _client(
            FakeTransport([FakeResponse(payload={"errors": graphql_errors})])
        ).request("query { shop { id } }")

    assert exc_info.value.graphql_errors == graphql_errors


def test_request_maps_invalid_response_shape_to_validation_error() -> None:
    with pytest.raises(ShopifyResponseValidationError):
        _client(FakeTransport([FakeResponse(payload={"data": []})])).request(
            "query { shop { id } }"
        )


def test_request_rejects_non_object_json_response() -> None:
    with pytest.raises(ShopifyResponseValidationError, match="root must be"):
        _client(FakeTransport([FakeResponse(payload=[])])).request(
            "query { shop { id } }"
        )


def test_root_clients_with_same_credentials_do_not_share_transports() -> None:
    first_transport = FakeTransport([_success_response({"shop": {"id": "first"}})])
    second_transport = FakeTransport([_success_response({"shop": {"id": "second"}})])
    first_client = _client(first_transport)
    second_client = _client(second_transport)

    first_response = first_client.request("query { shop { id } }")
    second_response = second_client.request("query { shop { id } }")

    assert first_response.data == {"shop": {"id": "first"}}
    assert second_response.data == {"shop": {"id": "second"}}
    assert len(first_transport.calls) == 1
    assert len(second_transport.calls) == 1


def test_wrapper_caches_one_root_client_with_its_transport() -> None:
    transport = FakeTransport([_success_response()])
    wrapper = ShopifyClientWrapper(
        "example.myshopify.com",
        "token",
        "2026-07",
        transport=transport,
    )

    assert wrapper.client is wrapper.client
    wrapper.request("query { shop { id } }")
    assert len(transport.calls) == 1


def test_client_context_accepts_injected_transport() -> None:
    transport = FakeTransport([_success_response()])

    with client_context(
        "example.myshopify.com",
        "token",
        "2026-07",
        transport=transport,
    ) as wrapper:
        wrapper.request("query { shop { id } }")

    assert len(transport.calls) == 1
