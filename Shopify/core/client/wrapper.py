from .root import RootClient


class ShopifyClientWrapper:
    def __init__(
        self,
        shop_domain: str,
        access_token: str
    ):
        self._shop_domain = shop_domain
        self._access_token = access_token
        self._client = None

    @property
    def client(self) -> RootClient:
        if not self._client:
            self._client = self._generate_client()
        return self._client
    
    def request(self, query: str, variables: dict = None) -> dict:
        res = self.client.request(query=query, variables=variables)
        return res
    
    def _generate_client(self) -> RootClient:
        try:
            client_instance = RootClient(
                shop_domain=self._shop_domain,
                access_token=self._access_token,
                api_version="2025-01"
            )
            return client_instance
        except Exception as e:
            return e
        