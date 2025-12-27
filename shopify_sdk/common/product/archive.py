from shopify_sdk import client
from shopify_sdk.gql import productUpdate
from shopify_sdk.gql.core.types import ProductUpdateInput, ProductStatus
from .types import ProductActionResponse
from shopify_sdk.gql.core.types import ID
from .query import product_by_sku


def archive_product_by_id(product_id: ID) -> ProductActionResponse:
    """
    Archive a product by its Shopify product ID using productUpdate mutation (status=ARCHIVED).
    Shopify docs: https://shopify.dev/docs/api/admin-graphql/2025-10/mutations/productUpdate
    """
    success = True
    message = f"Successfully archived product with ID '{product_id}'."
    try:
        update_input = ProductUpdateInput(id=product_id, status=ProductStatus.ARCHIVED)
        result = productUpdate(product=update_input).execute(client=client)
        if not result or result.get("userErrors") != []:
            success = False
            message = f"Failed to archive product with ID '{product_id}'."
    except Exception as e:
        success = False
        message = str(e)
    return ProductActionResponse(
        action="archive",
        success=success,
        message=message,
        sku=None,
    )


def archive_product_by_sku(sku: str) -> ProductActionResponse:
    """
    Archive a product by SKU using Shopify's productUpdate mutation (status=ARCHIVED).
    Shopify docs: https://shopify.dev/docs/api/admin-graphql/2025-10/mutations/productUpdate
    """
    product = product_by_sku(sku)
    if not product:
        raise ValueError(f"No product found for SKU '{sku}'.")
    
    product_id = product.id
    resp = archive_product_by_id(product_id)
    resp.sku = sku
    return resp

