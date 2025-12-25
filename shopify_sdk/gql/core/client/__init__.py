import os
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Iterator, Optional, cast

from dotenv import load_dotenv

from .wrapper import ShopifyClientWrapper as ShopifyClient
from .example import test
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

class _ClientProxy:
    __slots__ = ()

    def request(self, query: str, variables: Optional[Dict[Any, Any]] = None) -> GQLResponse:
        return _get_current_client().request(query=query, variables=variables)

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
    api_version: Optional[str] = None,
) -> Iterator[ShopifyClient]:
    """
    Temporarily set the active Shopify client for the current context.

    Within the context, the module-level ``client`` proxy uses the provided
    credentials. When the context exits, the previous client is restored.
    """
    wrapper = ShopifyClient(
        shop_domain=shop_domain,
        access_token=access_token,
        api_version=api_version,
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
    "test",
    "client",
    "client_context",
]
