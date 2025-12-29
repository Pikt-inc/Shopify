import os
from typing import Optional, Dict, Any
from .root import RootClient
from .types import GQLResponse


class ShopifyClientWrapper:
    def __init__(
        self, shop_domain: str, access_token: str, api_version: Optional[str] = None
    ):
        self._shop_domain = shop_domain
        self._access_token = access_token
        # Prefer explicit version, then env, then a modern default that supports newer fields.
        self._api_version = api_version or os.getenv("SHOPIFY_API_VERSION") or "2025-10"
        self._client: Optional[RootClient] = None

    @property
    def client(self) -> RootClient:
        if not self._client:
            self._client = self._generate_client()
        return self._client

    def request(
        self, query: str, variables: Optional[Dict[Any, Any]] = None
    ) -> GQLResponse:
        res = self.client.request(query=query, variables=variables)
        return res

    def _generate_client(self) -> RootClient:
        try:
            client_instance = RootClient(
                shop_domain=self._shop_domain,
                access_token=self._access_token,
                api_version=self._api_version,
            )
            return client_instance
        except Exception as e:
            raise ValueError("Failed to generate RootClient") from e
