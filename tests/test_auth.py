from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone

import pytest

from shopify_sdk.gql.core.client.auth import (
    TOKEN_REQUEST_TIMEOUT,
    ShopifyClientCredentials,
    ShopifyClientCredentialsTokenProvider,
    clear_cached_client_credentials_providers,
    get_cached_client_credentials_provider,
    StaticShopifyTokenProvider,
)
from shopify_sdk.gql.core.client.errors import ShopifyAuthenticationError


class FakeResponse:
    def __init__(self, status_code: int, payload: Mapping[str, object]) -> None:
        self.status_code = status_code
        self.headers: Mapping[str, str] = {}
        self.text = ""
        self._payload = payload

    def json(self) -> Mapping[str, object]:
        return self._payload


class FakeTokenTransport:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def post(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        data: Mapping[str, str],
        timeout: tuple[float, float],
    ) -> FakeResponse:
        self.calls.append(
            {
                "url": url,
                "headers": dict(headers),
                "data": dict(data),
                "timeout": timeout,
            }
        )
        return self.responses.pop(0)


def _credentials() -> ShopifyClientCredentials:
    return ShopifyClientCredentials(
        shop_domain="https://example.myshopify.com/",
        client_id="client-id",
        client_secret="client-secret",
    )


def test_static_provider_returns_existing_token() -> None:
    provider = StaticShopifyTokenProvider("access-token")

    assert provider.get_access_token() == "access-token"


def test_client_credentials_provider_requests_and_caches_token() -> None:
    transport = FakeTokenTransport(
        [FakeResponse(200, {"access_token": "access-token", "expires_in": 3600})]
    )
    provider = ShopifyClientCredentialsTokenProvider(
        _credentials(),
        transport=transport,
        now=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert provider.get_access_token() == "access-token"
    assert provider.get_access_token() == "access-token"
    assert len(transport.calls) == 1
    assert transport.calls[0] == {
        "url": "https://example.myshopify.com/admin/oauth/access_token",
        "headers": {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        "data": {
            "grant_type": "client_credentials",
            "client_id": "client-id",
            "client_secret": "client-secret",
        },
        "timeout": TOKEN_REQUEST_TIMEOUT,
    }
    assert provider.expires_at == datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(
        seconds=3600
    )


def test_client_credentials_provider_refreshes_inside_expiry_buffer() -> None:
    current_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    transport = FakeTokenTransport(
        [
            FakeResponse(200, {"access_token": "first-token", "expires_in": 1000}),
            FakeResponse(200, {"access_token": "second-token", "expires_in": 1000}),
        ]
    )
    provider = ShopifyClientCredentialsTokenProvider(
        _credentials(),
        transport=transport,
        now=lambda: current_time,
    )

    assert provider.get_access_token() == "first-token"
    current_time += timedelta(seconds=701)

    assert provider.get_access_token() == "second-token"
    assert len(transport.calls) == 2


def test_client_credentials_provider_hides_secret_in_authentication_error() -> None:
    transport = FakeTokenTransport([FakeResponse(401, {"error": "invalid_client"})])
    provider = ShopifyClientCredentialsTokenProvider(
        _credentials(),
        transport=transport,
    )

    with pytest.raises(ShopifyAuthenticationError) as error:
        provider.get_access_token()

    assert "client-secret" not in str(error.value)
    assert "invalid_client" not in str(error.value)


def test_client_credentials_provider_rejects_incomplete_response() -> None:
    transport = FakeTokenTransport([FakeResponse(200, {"access_token": "token"})])
    provider = ShopifyClientCredentialsTokenProvider(
        _credentials(),
        transport=transport,
    )

    with pytest.raises(ShopifyAuthenticationError):
        provider.get_access_token()


def test_cached_provider_is_reused_for_same_shop_and_client() -> None:
    clear_cached_client_credentials_providers()
    try:
        first = get_cached_client_credentials_provider(_credentials())
        second = get_cached_client_credentials_provider(_credentials())

        assert first is second
    finally:
        clear_cached_client_credentials_providers()
