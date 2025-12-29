from __future__ import annotations

from typing import Any

from shopify_sdk import client
from shopify_sdk.gql import (
    productCreate,
    productUpdate
)
from shopify_sdk.gql.core.types import (
    ProductCreateInput,
    ProductUpdateInput
)


def create_product(
    input: ProductCreateInput,
) -> str:
    """Create a new product using the provided ProductCreateInput."""
    result: dict[str, Any] = productCreate(
        product=input
    ).execute(client=client)
    product_id = result.get('product', {}).get('id', None)
    if not isinstance(product_id, str):
        raise ValueError("Product creation failed; no product ID returned.")
    return product_id


def update_product(
    input: ProductUpdateInput,
) -> str:
    result: dict[str, Any] = productUpdate(
        product=input
    ).execute(client=client)
    product_id = result.get('product', {}).get('id', None)
    if not isinstance(product_id, str):
        raise ValueError("Product creation failed; no product ID returned.")
    return product_id
