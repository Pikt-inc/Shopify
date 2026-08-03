import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, cast

from .auth import ShopifyTokenTransport
from .errors import (
    ShopifyAuthenticationError,
    ShopifyGraphQLError,
    ShopifyHttpError,
    ShopifyNetworkError,
    ShopifyResponseDecodeError,
    ShopifyResponseValidationError,
    ShopifyTransportError,
)
from .retry import RequestRetryMode, ShopifyRetryPolicy
from .transport import RequestsTransport, ShopifyHttpResponse, ShopifyTransport
from .types import (
    GQLCost,
    GQLExtensions,
    GQLRequestParams,
    GQLResponse,
    GQLThrottleStatus,
)
from .wrapper import ShopifyClientWrapper as ShopifyClient


def _build_env_client() -> ShopifyClient:
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN") or None
    client_id = os.getenv("SHOPIFY_CLIENT_ID") or None
    client_secret = os.getenv("SHOPIFY_CLIENT_SECRET") or None
    return ShopifyClient(
        shop_domain=os.getenv("SHOPIFY_SHOP_DOMAIN") or "",
        access_token=access_token,
        client_id=client_id,
        client_secret=client_secret,
        allow_unconfigured=True,
    )


_current_client: ContextVar[ShopifyClient | None] = ContextVar(
    "shopify_client",
    default=None,
)


def _get_current_client() -> ShopifyClient:
    current = _current_client.get()
    if current is not None:
        return current
    current = _build_env_client()
    _current_client.set(current)
    return current


def current_api_version() -> str:
    """Return the active Shopify Admin GraphQL API version for this context."""
    return _get_current_client().gql_version


class _ClientProxy:
    __slots__ = ()

    def request(
        self,
        query: str,
        variables: dict[str, object] | None = None,
        *,
        retry_mode: RequestRetryMode = RequestRetryMode.NEVER,
    ) -> GQLResponse:
        return _get_current_client().request(
            query=query,
            variables=variables,
            retry_mode=retry_mode,
        )

    def __getattr__(self, name: str):
        return getattr(_get_current_client(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(_get_current_client(), name, value)

    def __repr__(self) -> str:
        return repr(_get_current_client())

    def __str__(self) -> str:
        return str(_get_current_client())


@contextmanager
def client_context(
    shop_domain: str,
    access_token: str | None = None,
    api_version: str | None = None,
    *,
    client_id: str | None = None,
    client_secret: str | None = None,
    token_transport: ShopifyTokenTransport | None = None,
    transport: ShopifyTransport | None = None,
    retry_policy: ShopifyRetryPolicy | None = None,
) -> Iterator[ShopifyClient]:
    """
    Temporarily set the active Shopify client for the current context.

    Within the context, the module-level ``client`` proxy uses the provided
    credentials and API version. When the context exits, the previous client
    is restored.

    :param shop_domain: Shopify shop domain.
    :param access_token: Existing Shopify Admin API access token.
    :param api_version: Optional Shopify Admin GraphQL API version.
    :param client_id: Shopify app client ID for client-credentials auth.
    :param client_secret: Shopify app client secret for client-credentials auth.
    :param transport: Optional HTTP transport for the active client.
    :param retry_policy: Optional policy for safe read retries.
    """
    wrapper = ShopifyClient(
        shop_domain=shop_domain,
        access_token=access_token,
        api_version=api_version,
        client_id=client_id,
        client_secret=client_secret,
        token_transport=token_transport,
        transport=transport,
        retry_policy=retry_policy,
    )
    token = _current_client.set(wrapper)
    try:
        yield wrapper
    finally:
        _current_client.reset(token)


client = cast(ShopifyClient, _ClientProxy())

__all__ = [
    "GQLCost",
    "GQLExtensions",
    "GQLRequestParams",
    "GQLResponse",
    "GQLThrottleStatus",
    "RequestRetryMode",
    "RequestsTransport",
    "ShopifyAuthenticationError",
    "ShopifyClient",
    "ShopifyGraphQLError",
    "ShopifyHttpError",
    "ShopifyHttpResponse",
    "ShopifyNetworkError",
    "ShopifyResponseDecodeError",
    "ShopifyResponseValidationError",
    "ShopifyRetryPolicy",
    "ShopifyTransport",
    "ShopifyTransportError",
    "client",
    "client_context",
    "current_api_version",
]
