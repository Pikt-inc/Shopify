from typing import Any

from shopify_sdk import client
from shopify_sdk.gql import productUpdate, productVariants
from shopify_sdk.gql.core.types import ProductInput, ProductStatus


def _lookup_product_by_sku(
    sku: str,
) -> tuple[str, str | None]:
    """Return (product_id, product_title) for the first variant matching sku."""
    variant_connection = productVariants(
        first=1,
        query=f"sku:{sku}",
        field_inclusions={
            "ProductVariant": {"sku", "product"},
            "Product": {"id", "title"},
        },
    ).execute(client=client)

    if not variant_connection or not getattr(variant_connection, "nodes", None):
        raise ValueError(f"No product variant found for SKU '{sku}'.")

    variant = variant_connection.nodes[0]
    product = getattr(variant, "product", None)
    if not product or not getattr(product, "id", None):
        raise ValueError(f"Product lookup for SKU '{sku}' returned no product id.")

    return product.id, getattr(product, "title", None)


def archive_product_by_sku(sku: str) -> dict[str, Any]:
    """
    Archive a product by SKU using Shopify's productUpdate mutation (status=ARCHIVED).
    Shopify docs: https://shopify.dev/docs/api/admin-graphql/2025-10/mutations/productUpdate
    """
    product_id, product_title = _lookup_product_by_sku(sku)
    update_input = ProductInput(id=product_id, status=ProductStatus.ARCHIVED)
    result = productUpdate(input=update_input).execute(client=client)
    return {
        "productId": product_id,
        "sku": sku,
        "productTitle": product_title,
        "result": result,
    }
