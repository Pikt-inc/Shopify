import requests
import time
from typing import Optional, Dict, Any
from .singleton import SingletonBase
from .types import (
    GQLRequestParams,
    GQLResponse,
)

class RootClient(SingletonBase):

    def __init__(
        self,
        shop_domain: str,
        access_token: str,
        api_version: str
    ):
        self._shop_domain = shop_domain
        self._access_token = access_token
        self._api_version = api_version
        self._last_request_time = 0

    def check_limit(self) -> None:
        """
        Ensures that the request rate limit of 2 requests per second is not exceeded.
        If the limit is about to be exceeded, it waits for the required time.
        """
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        if time_since_last_request < 0.5:  # 0.5 seconds = 2 requests per second
            time.sleep(0.5 - time_since_last_request)

    def request(self, query: str, variables: Optional[Dict[Any, Any]] = None) -> GQLResponse:
        self.check_limit()  # Ensure rate limit is respected
        _params = GQLRequestParams(query=query, variables=variables)

        headers = {
            "Content-Type": "application/json",
            f"X-Shopify-Access-Token": f"{self._access_token}"
        }
        
        payload: Dict[str, Any] = {"query": query}
        if variables:
            if not isinstance(variables, dict):
                raise TypeError("variables must be a dictionary.")
            payload["variables"] = variables
        else:
            payload["variables"] = {}

        response = requests.post(
            self.graphql_request_url,
            headers=headers,
            json=payload
        )

        self._last_request_time = int(time.time())
        response_json = response.json()

        if "errors" in response_json:
            raise ValueError(f"GraphQL errors occurred: {response_json.get('errors')}")

        _response = GQLResponse(**response_json)
        return _response
    
    def _handle_errors(self, response: GQLResponse) -> None:
        if hasattr(response, "errors") and response.errors:
            error_messages = [error.message for error in response.errors]
            raise ValueError(f"GraphQL Errors: {error_messages}")

    @property
    def access_token(self) -> str:
        return self._access_token

    @property
    def graphql_request_url(self) -> str:
        return f"https://{self._shop_domain}/admin/api/{self._api_version}/graphql.json"

    @property
    def gql_version(self) -> str:
        return self._api_version
