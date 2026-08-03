from __future__ import annotations

from shopify_sdk.api_versions import resolve_api_version

from .auth import (
    ShopifyClientCredentials,
    ShopifyClientCredentialsTokenProvider,
    ShopifyTokenProvider,
    ShopifyTokenTransport,
    get_cached_client_credentials_provider,
)
from .retry import RequestRetryMode, ShopifyRetryPolicy
from .root import RootClient
from .transport import ShopifyTransport
from .types import GQLResponse


class ShopifyClientWrapper:
    """Context-scoped Shopify client that resolves static or expiring credentials."""

    def __init__(
        self,
        shop_domain: str,
        access_token: str | None = None,
        api_version: str | None = None,
        *,
        client_id: str | None = None,
        client_secret: str | None = None,
        transport: ShopifyTransport | None = None,
        retry_policy: ShopifyRetryPolicy | None = None,
        token_provider: ShopifyTokenProvider | None = None,
        token_transport: ShopifyTokenTransport | None = None,
        allow_unconfigured: bool = False,
    ) -> None:
        """Initialize a context-scoped client wrapper.

        :param shop_domain: Shopify shop domain.
        :param access_token: Existing Shopify Admin API access token.
        :param api_version: Optional Shopify Admin GraphQL API version.
        :param client_id: Shopify app client ID for client-credentials auth.
        :param client_secret: Shopify app client secret for client-credentials auth.
        :param transport: Optional HTTP transport for GraphQL requests.
        :param retry_policy: Optional policy for safe GraphQL query retries.
        :param token_provider: Optional advanced token provider for composition/tests.
        :raises ValueError: If credentials are missing, partial, or mixed.
        """
        self._shop_domain = shop_domain
        self._access_token = access_token
        self._token_provider = self._resolve_token_provider(
            shop_domain=shop_domain,
            access_token=access_token,
            client_id=client_id,
            client_secret=client_secret,
            token_provider=token_provider,
            token_transport=token_transport,
            allow_unconfigured=allow_unconfigured,
        )
        self._api_version = resolve_api_version(api_version)
        self._transport = transport
        self._retry_policy = retry_policy
        self._client: RootClient | None = None

    @property
    def client(self) -> RootClient:
        """Return the lazily-created root client."""
        if not self._client:
            self._client = self._generate_client()
        return self._client

    def request(
        self,
        query: str,
        variables: dict[str, object] | None = None,
        *,
        retry_mode: RequestRetryMode = RequestRetryMode.NEVER,
    ) -> GQLResponse:
        """Execute a GraphQL request through the cached root client."""
        return self.client.request(
            query=query,
            variables=variables,
            retry_mode=retry_mode,
        )

    @property
    def gql_version(self) -> str:
        """Return the Shopify Admin GraphQL API version used by this wrapper."""
        return self._api_version

    @property
    def access_token(self) -> str:
        """Return the current Shopify Admin API access token."""
        return self.client.access_token

    @staticmethod
    def _resolve_token_provider(
        *,
        shop_domain: str,
        access_token: str | None,
        client_id: str | None,
        client_secret: str | None,
        token_provider: ShopifyTokenProvider | None,
        token_transport: ShopifyTokenTransport | None,
        allow_unconfigured: bool,
    ) -> ShopifyTokenProvider | None:
        """Resolve one supported credential mode into a token provider."""
        has_client_id = client_id is not None
        has_client_secret = client_secret is not None
        has_client_credentials = has_client_id or has_client_secret
        if token_provider is not None and (access_token is not None or has_client_credentials):
            raise ValueError("Token provider cannot be combined with other credentials.")
        if access_token is not None and has_client_credentials:
            raise ValueError("Provide either access_token or client credentials, not both.")
        if has_client_id != has_client_secret:
            raise ValueError("Both client_id and client_secret are required together.")
        if token_provider is not None:
            return token_provider
        if access_token is not None:
            if not access_token.strip():
                raise ValueError("Shopify access token must not be blank.")
            return None
        if client_id is None or client_secret is None:
            if allow_unconfigured and access_token is None:
                return None
            raise ValueError(
                "Provide access_token or both client_id and client_secret."
            )
        credentials = ShopifyClientCredentials(
            shop_domain=shop_domain,
            client_id=client_id,
            client_secret=client_secret,
        )
        if token_transport is not None:
            return ShopifyClientCredentialsTokenProvider(
                credentials,
                transport=token_transport,
            )
        return get_cached_client_credentials_provider(credentials)

    def _generate_client(self) -> RootClient:
        try:
            client_instance = RootClient(
                shop_domain=self._shop_domain,
                access_token=self._access_token,
                api_version=self._api_version,
                transport=self._transport,
                retry_policy=self._retry_policy,
                token_provider=self._token_provider,
            )
            return client_instance
        except Exception as exc:
            raise ValueError("Failed to generate RootClient") from exc
