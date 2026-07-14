from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .types import GQLCost


@dataclass(frozen=True)
class ShopifyResponseMetadata:
    """Safe HTTP response metadata attached to Shopify transport errors."""

    status_code: int | None = None
    request_id: str | None = None
    retry_after: str | None = None
    content_type: str | None = None


class ShopifyTransportError(ValueError):
    """Base error for safe, structured Shopify transport failures."""

    def __init__(
        self,
        message: str,
        *,
        metadata: ShopifyResponseMetadata | None = None,
    ) -> None:
        """Initialize a transport failure without retaining raw response content.

        :param message: Safe human-readable error description.
        :param metadata: Safe HTTP response metadata, when a response was received.
        """
        response_metadata = metadata or ShopifyResponseMetadata()
        self.status_code = response_metadata.status_code
        self.request_id = response_metadata.request_id
        self.retry_after = response_metadata.retry_after
        self.content_type = response_metadata.content_type
        super().__init__(message)


class ShopifyNetworkError(ShopifyTransportError):
    """Raised when no Shopify HTTP response was received from the transport."""


class ShopifyHttpError(ShopifyTransportError):
    """Raised for non-successful Shopify HTTP responses."""


class ShopifyResponseDecodeError(ShopifyTransportError):
    """Raised when a successful Shopify response is not valid JSON."""


class ShopifyGraphQLError(ShopifyTransportError):
    """Raised when Shopify returns top-level GraphQL errors."""

    def __init__(
        self,
        errors: Sequence[object],
        *,
        metadata: ShopifyResponseMetadata | None = None,
        cost: GQLCost | None = None,
    ) -> None:
        """Initialize a GraphQL error with structured error entries.

        :param errors: Top-level GraphQL error entries returned by Shopify.
        :param metadata: Safe HTTP response metadata.
        """
        self.graphql_errors = list(errors)
        self.cost = cost
        super().__init__("Shopify returned GraphQL errors.", metadata=metadata)

    @property
    def is_throttled(self) -> bool:
        """Return whether Shopify identified this GraphQL failure as throttling."""
        from .retry import is_throttled_graphql_error

        return is_throttled_graphql_error(self.graphql_errors)


class ShopifyResponseValidationError(ShopifyTransportError):
    """Raised when a successful Shopify response fails SDK model validation."""
