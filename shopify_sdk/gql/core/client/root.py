from __future__ import annotations

import time
from collections.abc import Mapping
from typing import cast

from pydantic import ValidationError
from requests.exceptions import RequestException

from shopify_sdk.gql.core.client.errors import ShopifyGraphQLError
from shopify_sdk.gql.core.client.errors import ShopifyHttpError
from shopify_sdk.gql.core.client.errors import ShopifyResponseDecodeError
from shopify_sdk.gql.core.client.errors import ShopifyResponseMetadata
from shopify_sdk.gql.core.client.errors import ShopifyResponseValidationError
from shopify_sdk.gql.core.client.errors import ShopifyTransportError
from shopify_sdk.gql.core.client.transport import RequestsTransport
from shopify_sdk.gql.core.client.transport import ShopifyHttpResponse
from shopify_sdk.gql.core.client.transport import ShopifyTransport
from shopify_sdk.gql.core.client.types import GQLRequestParams
from shopify_sdk.gql.core.client.types import GQLResponse


class RootClient:
    """Low-level Shopify Admin GraphQL client with an injectable HTTP transport."""

    REQUEST_TIMEOUT = (10.0, 30.0)

    def __init__(
        self,
        shop_domain: str,
        access_token: str,
        api_version: str,
        transport: ShopifyTransport | None = None,
    ) -> None:
        """Initialize a Shopify client for one shop and Admin API version.

        :param shop_domain: Shopify shop domain.
        :param access_token: Shopify Admin API access token.
        :param api_version: Shopify Admin GraphQL API version.
        :param transport: Optional HTTP transport used for GraphQL requests.
        """
        self._shop_domain = shop_domain
        self._access_token = access_token
        self._api_version = api_version
        self._transport = transport or RequestsTransport()
        self._last_request_time = 0.0

    def check_limit(self) -> None:
        """Apply the existing fixed two-requests-per-second pacing guard."""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        if time_since_last_request < 0.5:
            time.sleep(0.5 - time_since_last_request)

    def request(
        self,
        query: str,
        variables: dict[str, object] | None = None,
    ) -> GQLResponse:
        """Execute one Shopify Admin GraphQL request through the configured transport.

        :param query: GraphQL query or mutation document.
        :param variables: GraphQL variable mapping.
        :returns: Validated Shopify GraphQL response.
        :raises ShopifyTransportError: If request transport or response handling fails.
        """
        self.check_limit()
        parameters = GQLRequestParams(query=query, variables=variables)
        response = self._post(parameters)
        self._last_request_time = time.time()
        self._raise_for_http_error(response)
        response_json = self._decode_response(response)
        self._raise_for_graphql_errors(response_json, response)
        return self._validate_response(response_json, response)

    def _post(self, parameters: GQLRequestParams) -> ShopifyHttpResponse:
        """Send one GraphQL request and normalize network failures.

        :param parameters: GraphQL document and variable mapping.
        :returns: HTTP response from the configured transport.
        :raises ShopifyTransportError: If the request cannot be sent.
        """
        try:
            return cast(
                ShopifyHttpResponse,
                self._transport.post(
                    self.graphql_request_url,
                    headers=self._headers,
                    json={
                        "query": parameters.query,
                        "variables": parameters.variables or {},
                    },
                    timeout=self.REQUEST_TIMEOUT,
                ),
            )
        except RequestException as exc:
            raise ShopifyTransportError("Shopify transport request failed.") from exc

    def _raise_for_http_error(self, response: ShopifyHttpResponse) -> None:
        """Raise a safe structured error for a non-2xx HTTP response."""
        if 200 <= response.status_code < 300:
            return
        raise ShopifyHttpError(
            f"Shopify HTTP request failed with status {response.status_code}.",
            metadata=self._response_metadata(response),
        )

    def _decode_response(
        self,
        response: ShopifyHttpResponse,
    ) -> Mapping[str, object]:
        """Decode a successful response as JSON without exposing its raw body."""
        try:
            response_json = response.json()
        except ValueError as exc:
            raise ShopifyResponseDecodeError(
                "Shopify response was not valid JSON.",
                metadata=self._response_metadata(response),
            ) from exc
        if not isinstance(response_json, Mapping):
            raise ShopifyResponseValidationError(
                "Shopify response root must be a JSON object.",
                metadata=self._response_metadata(response),
            )
        return response_json

    def _raise_for_graphql_errors(
        self,
        response_json: Mapping[str, object],
        response: ShopifyHttpResponse,
    ) -> None:
        """Raise structured errors for top-level Shopify GraphQL failures."""
        errors = response_json.get("errors")
        if errors is not None:
            graphql_errors = errors if isinstance(errors, list) else [errors]
            raise ShopifyGraphQLError(
                graphql_errors,
                metadata=self._response_metadata(response),
            )

    def _validate_response(
        self,
        response_json: Mapping[str, object],
        response: ShopifyHttpResponse,
    ) -> GQLResponse:
        """Validate a decoded Shopify GraphQL response against SDK response models."""
        try:
            return GQLResponse.model_validate(response_json)
        except ValidationError as exc:
            raise ShopifyResponseValidationError(
                "Shopify response did not match the SDK response schema.",
                metadata=self._response_metadata(response),
            ) from exc

    def _response_metadata(
        self,
        response: ShopifyHttpResponse,
    ) -> ShopifyResponseMetadata:
        """Return safe, case-insensitive response metadata for errors."""
        return ShopifyResponseMetadata(
            status_code=response.status_code,
            request_id=self._header(response.headers, "X-Request-ID"),
            retry_after=self._header(response.headers, "Retry-After"),
            content_type=self._header(response.headers, "Content-Type"),
        )

    def _header(self, headers: Mapping[str, str], name: str) -> str | None:
        """Return a case-insensitive HTTP header value.

        :param headers: HTTP response headers.
        :param name: Header name to resolve.
        :returns: Header value when present.
        """
        normalized_name = name.casefold()
        return next(
            (
                value
                for header_name, value in headers.items()
                if header_name.casefold() == normalized_name
            ),
            None,
        )

    @property
    def _headers(self) -> dict[str, str]:
        """Return Admin GraphQL request headers without exposing mutable state."""
        return {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": self._access_token,
        }

    @property
    def access_token(self) -> str:
        """Return the configured Shopify Admin API access token."""
        return self._access_token

    @property
    def graphql_request_url(self) -> str:
        """Return the Shopify Admin GraphQL endpoint for this client."""
        return f"https://{self._shop_domain}/admin/api/{self._api_version}/graphql.json"

    @property
    def gql_version(self) -> str:
        """Return the Shopify Admin GraphQL API version for this client."""
        return self._api_version
