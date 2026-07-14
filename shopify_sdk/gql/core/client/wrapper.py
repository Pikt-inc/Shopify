from typing import Optional

from shopify_sdk.api_versions import resolve_api_version

from .root import RootClient
from .retry import RequestRetryMode
from .retry import ShopifyRetryPolicy
from .transport import ShopifyTransport
from .types import GQLResponse


class ShopifyClientWrapper:
    def __init__(
        self,
        shop_domain: str,
        access_token: str,
        api_version: Optional[str] = None,
        *,
        transport: ShopifyTransport | None = None,
        retry_policy: ShopifyRetryPolicy | None = None,
    ) -> None:
        """Initialize a context-scoped client wrapper.

        :param shop_domain: Shopify shop domain.
        :param access_token: Shopify Admin API access token.
        :param api_version: Optional Shopify Admin GraphQL API version.
        :param transport: Optional HTTP transport for the generated root client.
        :param retry_policy: Optional policy for safe read retries.
        """
        self._shop_domain = shop_domain
        self._access_token = access_token
        # Prefer explicit version, then env, then a modern default that supports newer fields.
        self._api_version = resolve_api_version(api_version)
        self._transport = transport
        self._retry_policy = retry_policy
        self._client: Optional[RootClient] = None

    @property
    def client(self) -> RootClient:
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
        res = self.client.request(
            query=query,
            variables=variables,
            retry_mode=retry_mode,
        )
        return res

    @property
    def gql_version(self) -> str:
        """Return the Shopify Admin GraphQL API version used by this wrapper."""
        return self._api_version

    def _generate_client(self) -> RootClient:
        try:
            client_instance = RootClient(
                shop_domain=self._shop_domain,
                access_token=self._access_token,
                api_version=self._api_version,
                transport=self._transport,
                retry_policy=self._retry_policy,
            )
            return client_instance
        except Exception as e:
            raise ValueError("Failed to generate RootClient") from e
