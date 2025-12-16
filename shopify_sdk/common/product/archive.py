from shopify_sdk import client
from shopify_sdk.gql import productUpdate
from shopify_sdk.gql.core.types import ProductUpdateInput, ProductStatus
from .types import ProductActionResponse
from .query import product_by_sku


def archive_product_by_sku(sku: str) -> ProductActionResponse:
    """
    Archive a product by SKU using Shopify's productUpdate mutation (status=ARCHIVED).
    Shopify docs: https://shopify.dev/docs/api/admin-graphql/2025-10/mutations/productUpdate
    """
    success = True
    message = f"Successfully archived product for SKU '{sku}'."
    try:
        product = product_by_sku(sku)
        if not product:
            raise ValueError(f"No product found for SKU '{sku}'.")
        
        product_id = product.id
        product_title = getattr(product, "title", None)
        update_input = ProductUpdateInput(id=product_id, status=ProductStatus.ARCHIVED)
        result = productUpdate(product=update_input).execute(client=client)
        if not result or result.get("userErrors") != []:
            success = False
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
