import os
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterator, cast

from dotenv import load_dotenv

from .wrapper import ShopifyClientWrapper as ShopifyClient
from .errors import ShopifyGraphQLError
from .errors import ShopifyHttpError
from .errors import ShopifyNetworkError
from .errors import ShopifyResponseDecodeError
from .errors import ShopifyResponseValidationError
from .errors import ShopifyTransportError
from .transport import RequestsTransport
from .transport import ShopifyHttpResponse
from .transport import ShopifyTransport
from .retry import RequestRetryMode
from .retry import ShopifyRetryPolicy
from .types import (
    GQLRequestParams,
    GQLResponse,
    GQLCost,
    GQLThrottleStatus,
    GQLExtensions,
)

load_dotenv()


def _build_env_client() -> ShopifyClient:
    return ShopifyClient(
        shop_domain=os.getenv("SHOPIFY_SHOP_DOMAIN") or "",
        access_token=os.getenv("SHOPIFY_ACCESS_TOKEN") or "",
    )


_current_client: ContextVar[ShopifyClient] = ContextVar(
    "shopify_client",
    default=_build_env_client(),
)


def _get_current_client() -> ShopifyClient:
    return _current_client.get()


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
    access_token: str,
    api_version: str,
    *,
    transport: ShopifyTransport | None = None,
    retry_policy: ShopifyRetryPolicy | None = None,
) -> Iterator[ShopifyClient]:
    """
    Temporarily set the active Shopify client for the current context.

    Within the context, the module-level ``client`` proxy uses the provided
    credentials and API version. When the context exits, the previous client
    is restored.

    :param shop_domain: Shopify shop domain.
    :param access_token: Shopify Admin API access token.
    :param api_version: Shopify Admin GraphQL API version.
    :param transport: Optional HTTP transport for the active client.
    :param retry_policy: Optional policy for safe read retries.
    """
    wrapper = ShopifyClient(
        shop_domain=shop_domain,
        access_token=access_token,
        api_version=api_version,
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
    "ShopifyClient",
    "GQLRequestParams",
    "GQLResponse",
    "GQLCost",
    "GQLThrottleStatus",
    "GQLExtensions",
    "RequestsTransport",
    "ShopifyGraphQLError",
    "ShopifyHttpError",
    "ShopifyNetworkError",
    "ShopifyHttpResponse",
    "client",
    "client_context",
    "current_api_version",
    "ShopifyResponseDecodeError",
    "ShopifyResponseValidationError",
    "ShopifyTransport",
    "ShopifyTransportError",
    "RequestRetryMode",
    "ShopifyRetryPolicy",
]
