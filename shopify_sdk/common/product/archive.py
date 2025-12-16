from shopify_sdk import client
from shopify_sdk.gql import productUpdate, productVariants
from shopify_sdk.gql.core.types import ProductUpdateInput, ProductStatus
from .types import ProductActionResponse
from .query import product_by_sku


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


def archive_product_by_sku(sku: str) -> ProductActionResponse:
    """
    Archive a product by SKU using Shopify's productUpdate mutation (status=ARCHIVED).
    Shopify docs: https://shopify.dev/docs/api/admin-graphql/2025-10/mutations/productUpdate
    """
    success = False
    message: str | None = None
    try:
        product = product_by_sku(sku)
        if not product:
            raise ValueError(f"No product found for SKU '{sku}'.")
        
        product_id = product.id
        product_title = getattr(product, "title", None)
        update_input = ProductUpdateInput(id=product_id, status=ProductStatus.ARCHIVED)
        result = productUpdate(product=update_input).execute(client=client)
        success = bool(result and getattr(result, "product", None))
        if not success:
            label = product_title or product_id
            message = f"Failed to archive product '{label}' for SKU '{sku}'."
    except Exception as e:
        success = False
        message = str(e)
    return ProductActionResponse(
        action="archive",
        success=success,
        message=message,
        sku=sku,
    )
