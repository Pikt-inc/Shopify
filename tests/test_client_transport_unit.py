from __future__ import annotations

from collections.abc import Mapping
from typing import cast

import pytest
from requests.exceptions import ConnectTimeout
from requests.exceptions import ReadTimeout

from shopify_sdk.gql.core.client import ShopifyGraphQLError
from shopify_sdk.gql.core.client import ShopifyHttpError
from shopify_sdk.gql.core.client import ShopifyResponseDecodeError
from shopify_sdk.gql.core.client import ShopifyResponseValidationError
from shopify_sdk.gql.core.client import ShopifyTransportError
from shopify_sdk.gql.core.client import client_context
from shopify_sdk.gql.core.client.root import RootClient
from shopify_sdk.gql.core.client.transport import ShopifyHttpResponse
from shopify_sdk.gql.core.client.wrapper import ShopifyClientWrapper


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


def _client(transport: FakeTransport) -> RootClient:
    return RootClient(
        shop_domain="example.myshopify.com",
        access_token="token",
        api_version="2026-07",
        transport=transport,
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
