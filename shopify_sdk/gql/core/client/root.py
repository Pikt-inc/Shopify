from __future__ import annotations

import random
import time
from collections.abc import Mapping
from collections.abc import Callable
from typing import cast

from pydantic import ValidationError
from requests.exceptions import RequestException

from shopify_sdk.gql.core.client.errors import ShopifyGraphQLError
from shopify_sdk.gql.core.client.errors import ShopifyHttpError
from shopify_sdk.gql.core.client.errors import ShopifyNetworkError
from shopify_sdk.gql.core.client.errors import ShopifyResponseDecodeError
from shopify_sdk.gql.core.client.errors import ShopifyResponseMetadata
from shopify_sdk.gql.core.client.errors import ShopifyResponseValidationError
from shopify_sdk.gql.core.client.errors import ShopifyTransportError
from shopify_sdk.gql.core.client.transport import RequestsTransport
from shopify_sdk.gql.core.client.transport import ShopifyHttpResponse
from shopify_sdk.gql.core.client.transport import ShopifyTransport
from shopify_sdk.gql.core.client.retry import RequestRetryMode
from shopify_sdk.gql.core.client.retry import ShopifyRetryDecider
from shopify_sdk.gql.core.client.retry import ShopifyRetryPolicy
from shopify_sdk.gql.core.client.types import GQLExtensions
from shopify_sdk.gql.core.client.types import GQLCost
from shopify_sdk.gql.core.client.types import GQLRequestParams
from shopify_sdk.gql.core.client.types import GQLResponse


class RootClient:
    """Low-level Shopify Admin GraphQL client with an injectable HTTP transport."""

    REQUEST_TIMEOUT = (10.0, 30.0)
    MIN_REQUEST_INTERVAL_S = 0.5

    def __init__(
        self,
        shop_domain: str,
        access_token: str,
        api_version: str,
        transport: ShopifyTransport | None = None,
        retry_policy: ShopifyRetryPolicy | None = None,
        sleep: Callable[[float], None] = time.sleep,
        monotonic_clock: Callable[[], float] = time.monotonic,
        random_value: Callable[[], float] = random.random,
    ) -> None:
        """Initialize a Shopify client for one shop and Admin API version.

        :param shop_domain: Shopify shop domain.
        :param access_token: Shopify Admin API access token.
        :param api_version: Shopify Admin GraphQL API version.
        :param transport: Optional HTTP transport used for GraphQL requests.
        :param retry_policy: Optional policy for safe read retries.
        :param sleep: Injectable delay function used for pacing and retries.
        :param monotonic_clock: Injectable monotonic clock used for request pacing.
        :param random_value: Injectable unit-interval source used for retry jitter.
        """
        self._shop_domain = shop_domain
        self._access_token = access_token
        self._api_version = api_version
        self._transport = transport or RequestsTransport()
        self._retry_policy = retry_policy or ShopifyRetryPolicy()
        self._retry_decider = ShopifyRetryDecider(self._retry_policy, random_value)
        self._sleep = sleep
        self._monotonic_clock = monotonic_clock
        self._last_request_time: float | None = None

    def check_limit(self) -> None:
        """Apply the existing fixed two-requests-per-second pacing guard."""
        if self._last_request_time is None:
            return
        current_time = self._monotonic_clock()
        time_since_last_request = current_time - self._last_request_time
        if time_since_last_request < self.MIN_REQUEST_INTERVAL_S:
            self._sleep(self.MIN_REQUEST_INTERVAL_S - time_since_last_request)

    def request(
        self,
        query: str,
        variables: dict[str, object] | None = None,
        *,
        retry_mode: RequestRetryMode = RequestRetryMode.NEVER,
    ) -> GQLResponse:
        """Execute one Shopify Admin GraphQL request through the configured transport.

        :param query: GraphQL query or mutation document.
        :param variables: GraphQL variable mapping.
        :param retry_mode: Whether the caller permits automatic retry for this request.
        :returns: Validated Shopify GraphQL response.
        :raises ShopifyTransportError: If request transport or response handling fails.
        """
        parameters = GQLRequestParams(query=query, variables=variables)
        return self._request_with_retry(parameters, retry_mode)

    def _request_with_retry(
        self,
        parameters: GQLRequestParams,
        retry_mode: RequestRetryMode,
    ) -> GQLResponse:
        """Execute attempts until a safe retry policy accepts or rejects a failure."""
        failed_attempt = 0
        while True:
            try:
                return self._request_once(parameters)
            except ShopifyTransportError as error:
                failed_attempt += 1
                decision = self._retry_decider.decide(
                    error=error,
                    retry_mode=retry_mode,
                    failed_attempt=failed_attempt,
                )
                if decision is None:
                    raise
                self._sleep(decision.delay_seconds)

    def _request_once(self, parameters: GQLRequestParams) -> GQLResponse:
        """Execute one fully validated request attempt through the Shopify transport."""
        self.check_limit()
        response = self._post(parameters)
        self._last_request_time = self._monotonic_clock()
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
            raise ShopifyNetworkError("Shopify transport request failed.") from exc

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
                cost=self._response_cost(response_json),
            )

    @staticmethod
    def _response_cost(response_json: Mapping[str, object]) -> GQLCost | None:
        """Extract valid Shopify cost metadata from successful or error responses."""
        extensions = response_json.get("extensions")
        if not isinstance(extensions, Mapping):
            return None
        try:
            return GQLExtensions.model_validate(extensions).cost
        except ValidationError:
            return None

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
