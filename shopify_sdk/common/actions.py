from __future__ import annotations

from shopify_sdk.common.proxy_product_service import calculate_inventory_delta
from shopify_sdk.common.proxy_product_service import ProductCreateWorkflow
from shopify_sdk.common.proxy_product_service import ProductUpdateWorkflow

from .types import ProxyProduct


class ProductCreate(ProductCreateWorkflow):
    """Backward-compatible public name for the proxy product create workflow."""


class ProductUpdate(ProductUpdateWorkflow):
    """Backward-compatible public name for the proxy product update workflow."""


def _calculate_inventory_delta(
    desired_quantity: int | None,
    current_quantity: int | None,
) -> int:
    """Return the inventory delta needed to reach the desired quantity."""
    return calculate_inventory_delta(desired_quantity, current_quantity)


def create_product(product: ProxyProduct) -> str:
    """Create a Shopify product from a proxy product and return its ID."""
    try:
        pc = ProductCreate.execute(proxy_product=product)
        return pc.product_id
    except Exception as exc:
        raise ValueError(f"Product creation failed: {exc}") from exc


def update_product(product: ProxyProduct) -> str:
    """Update a Shopify product from a proxy product and return its ID."""
    try:
        pu = ProductUpdate.execute(proxy_product=product)
        return pu.product_id
    except Exception as exc:
        raise ValueError(f"Product update failed: {exc}") from exc


__all__ = [
    "ProductCreate",
    "ProductUpdate",
    "_calculate_inventory_delta",
    "create_product",
    "update_product",
]
