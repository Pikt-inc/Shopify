import os
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

client = ShopifyClient(
    shop_domain=os.getenv("SHOPIFY_SHOP_DOMAIN"),
    access_token=os.getenv("SHOPIFY_ACCESS_TOKEN")
)

__all__ = [
    "ShopifyClient",
    "GQLRequestParams",
    "GQLResponse",
    "GQLCost",
    "GQLThrottleStatus",
    "GQLExtensions",
    "test",
    "client"
]