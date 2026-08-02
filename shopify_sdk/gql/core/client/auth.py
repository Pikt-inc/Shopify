from __future__ import annotations

import hmac
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Protocol, cast

import requests
from requests import Session
from requests.exceptions import RequestException

from .errors import ShopifyAuthenticationError, ShopifyResponseMetadata
from .transport import ShopifyHttpResponse

TOKEN_EXPIRY_SKEW_SECONDS = 300
TOKEN_REQUEST_TIMEOUT = (10.0, 30.0)


class ShopifyTokenProvider(Protocol):
    """Provide a current Shopify Admin API access token."""

    def get_access_token(self) -> str:
        """Return a valid access token for the configured Shopify shop."""


@dataclass(frozen=True)
class ShopifyClientCredentials:
    """Credentials used by Shopify's client-credentials grant."""

    shop_domain: str
    client_id: str
    client_secret: str = field(repr=False)

    def __post_init__(self) -> None:
        """Reject incomplete client credentials before any network request."""
        if not self.shop_domain.strip():
            raise ValueError("Shopify shop domain must not be blank.")
        if not self.client_id.strip():
            raise ValueError("Shopify client ID must not be blank.")
        if not self.client_secret.strip():
            raise ValueError("Shopify client secret must not be blank.")


class ShopifyTokenTransport(Protocol):
    """HTTP boundary for Shopify token endpoint requests."""

    def post(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        data: Mapping[str, str],
        timeout: tuple[float, float],
    ) -> ShopifyHttpResponse:
        """Post form-encoded token request data and return the response."""


class RequestsTokenTransport:
    """Requests-backed transport for Shopify token endpoint calls."""

    def __init__(self, session: Session | None = None) -> None:
        """Initialize the transport with an optional reusable session."""
        self._session = session or requests.Session()

    def post(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        data: Mapping[str, str],
        timeout: tuple[float, float],
    ) -> ShopifyHttpResponse:
        """Send a form-encoded token request."""
        return cast(
            ShopifyHttpResponse,
            self._session.post(
                url,
                headers=dict(headers),
                data=dict(data),
                timeout=timeout,
            ),
        )


class StaticShopifyTokenProvider:
    """Return a caller-supplied Shopify access token without network calls."""

    def __init__(self, access_token: str) -> None:
        """Initialize the provider with an existing access token."""
        if not access_token:
            raise ValueError("Shopify access token must not be blank.")
        self._access_token = access_token

    def get_access_token(self) -> str:
        """Return the configured access token."""
        return self._access_token


class ShopifyClientCredentialsTokenProvider:
    """Cache and refresh a Shopify client-credentials access token."""

    def __init__(
        self,
        credentials: ShopifyClientCredentials,
        *,
        transport: ShopifyTokenTransport | None = None,
        now: Callable[[], datetime] | None = None,
        expiry_skew_seconds: int = TOKEN_EXPIRY_SKEW_SECONDS,
    ) -> None:
        """Initialize a provider for one Shopify installation.

        :param credentials: Shopify shop and client credentials.
        :param transport: Optional token endpoint transport.
        :param now: Injectable UTC clock used by expiry checks.
        :param expiry_skew_seconds: Starting refresh buffer before expiration.
        """
        if expiry_skew_seconds < 0:
            raise ValueError("Token expiry skew must not be negative.")
        self._credentials = credentials
        self._transport: ShopifyTokenTransport = transport or RequestsTokenTransport()
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._expiry_skew_seconds = expiry_skew_seconds
        self._access_token: str | None = None
        self._expires_at: datetime | None = None
        self._lock = threading.RLock()

    @property
    def expires_at(self) -> datetime | None:
        """Return the cached token expiration time, when available."""
        return self._expires_at

    def get_access_token(self) -> str:
        """Return a cached token or obtain a replacement before expiry."""
        with self._lock:
            current_time = self._now()
            if self._has_valid_token(current_time):
                return self._access_token or ""
            self._refresh(current_time)
            return self._access_token or ""

    def matches_secret(self, client_secret: str) -> bool:
        """Return whether the provider belongs to the supplied client secret."""
        return hmac.compare_digest(self._credentials.client_secret, client_secret)

    def _has_valid_token(self, current_time: datetime) -> bool:
        if not self._access_token or self._expires_at is None:
            return False
        refresh_at = self._expires_at - timedelta(seconds=self._expiry_skew_seconds)
        return current_time < refresh_at

    def _refresh(self, current_time: datetime) -> None:
        response = self._request_token()
        token_response = self._parse_token_response(response)
        self._access_token = token_response.access_token
        self._expires_at = current_time + timedelta(
            seconds=token_response.expires_in
        )

    def _request_token(self) -> ShopifyHttpResponse:
        try:
            return self._transport.post(
                self._token_url,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._credentials.client_id,
                    "client_secret": self._credentials.client_secret,
                },
                timeout=TOKEN_REQUEST_TIMEOUT,
            )
        except RequestException as exc:
            raise ShopifyAuthenticationError(
                "Shopify access-token request failed.",
            ) from exc

    @property
    def _token_url(self) -> str:
        return (
            f"https://{normalize_shop_domain(self._credentials.shop_domain)}"
            "/admin/oauth/access_token"
        )

    def _parse_token_response(
        self,
        response: ShopifyHttpResponse,
    ) -> ShopifyTokenResponse:
        metadata = ShopifyResponseMetadata(status_code=response.status_code)
        if not 200 <= response.status_code < 300:
            raise ShopifyAuthenticationError(
                "Shopify rejected the client-credentials request.",
                metadata=metadata,
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise ShopifyAuthenticationError(
                "Shopify returned an invalid access-token response.",
                metadata=metadata,
            ) from exc
        if not isinstance(payload, Mapping):
            raise ShopifyAuthenticationError(
                "Shopify returned an invalid access-token response.",
                metadata=metadata,
            )
        return ShopifyTokenResponse.from_payload(payload, metadata=metadata)


@dataclass(frozen=True)
class ShopifyTokenResponse:
    """Validated token response returned by Shopify."""

    access_token: str
    expires_in: int

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
        *,
        metadata: ShopifyResponseMetadata,
    ) -> ShopifyTokenResponse:
        """Validate the token response without retaining raw response content."""
        access_token = payload.get("access_token")
        expires_in = payload.get("expires_in")
        if (
            not isinstance(access_token, str)
            or not access_token
            or isinstance(expires_in, bool)
            or not isinstance(expires_in, (int, float))
            or expires_in <= 0
        ):
            raise ShopifyAuthenticationError(
                "Shopify returned an incomplete access-token response.",
                metadata=metadata,
            )
        return cls(access_token=access_token, expires_in=int(expires_in))


_provider_cache: dict[tuple[str, str], ShopifyClientCredentialsTokenProvider] = {}
_provider_cache_lock = threading.RLock()


def get_cached_client_credentials_provider(
    credentials: ShopifyClientCredentials,
) -> ShopifyClientCredentialsTokenProvider:
    """Return the process-local token provider for one shop and client ID."""
    cache_key = (normalize_shop_domain(credentials.shop_domain), credentials.client_id)
    with _provider_cache_lock:
        provider = _provider_cache.get(cache_key)
        if provider is None or not provider.matches_secret(credentials.client_secret):
            provider = ShopifyClientCredentialsTokenProvider(credentials)
            _provider_cache[cache_key] = provider
        return provider


def clear_cached_client_credentials_providers() -> None:
    """Clear process-local providers, primarily for isolated test setup."""
    with _provider_cache_lock:
        _provider_cache.clear()


def normalize_shop_domain(shop_domain: str) -> str:
    """Normalize a Shopify domain for token endpoint URL construction."""
    return shop_domain.strip().removeprefix("https://").removeprefix("http://").rstrip("/")
