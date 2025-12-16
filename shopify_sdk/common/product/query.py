import logging

from shopify_sdk import client
from shopify_sdk.gql.queries import productByIdentifier, productVariants
from shopify_sdk.gql.core.types import *

logger = logging.getLogger(__name__)

def product_details(
    product_id: str
) -> Product:
    product: Product = productByIdentifier(
        identifier=ProductIdentifierInput(
            id=product_id,
            handle=None
        ),
        field_exclusions={
            "Product": Product.fields_except(
                exclude={
                    "id", "title", "descriptionHtml", "vendor", "productType", "tags",
                    "seo", "metafields", "status", "vendor", "variants"
                }
            ),
            "MetafieldConnection": {"edges", "pageInfo"},
            "ProductVariantConnection": ProductVariantConnection.fields_except(
                exclude={"nodes"}
            ),
            "ProductVariant": ProductVariant.fields_except(
                exclude={"id", "sku", "price", "inventoryQuantity"}
            ),
        },
    ).execute(client=client)

    if not product:
        logger.error(f"No product found for ID '{product_id}'.")
        raise ValueError(f"No product found for ID '{product_id}'.")

    return product

def variants_by_product(
    product_id: str,
) -> ProductVariantConnection:
    """Return all variants for the given product ID."""
    product: Product = productByIdentifier(
        identifier=ProductIdentifierInput(
            id=product_id,
            handle=None
        ),
        field_exclusions={
            "Product": Product.fields_except(
                exclude={"id", "variants"}
            ),
            "ProductVariantConnection": ProductVariantConnection.fields_except(
                exclude={"nodes"}
            ),
            "ProductVariant": ProductVariant.fields_except(
                exclude={"id", "title", "sku", "price", 'inventoryItem'}
            ),
            "InventoryItem": InventoryItem.fields_except(
                exclude={"id"}
            ),
        },
    ).execute(client=client)

    if not product or not product.variants:
        logger.error(f"No variants found for product ID '{product_id}'.")
        raise ValueError(f"No variants found for product ID '{product_id}'.")

    return product.variants


def product_by_sku(
    sku: str,
) -> Product:
    """Return (product_id, product_title) for the first variant matching sku."""
    variant_connection: ProductVariantConnection = productVariants(
        first=1,
        query=f"sku:{sku}",
        field_inclusions={
            "ProductVariant": {"sku", "product"},
            "Product": {"id", "title", "descriptionHtml", "vendor", "productType", "tags", "seo", "metafields", "variants"},
            "MetafieldConnection": {"nodes"},
            "Metafield": {"id", "key", "namespace", "type", "value"},
            "SEO": {"title", "description"},
            "ProductVariantConnection": {"nodes"},
        },
    ).execute(client=client)

    if not variant_connection or not getattr(variant_connection, "nodes", None):
        logger.error(f"No product variant found for SKU '{sku}'.")
        raise ValueError(f"No product variant found for SKU '{sku}'.")
    
    variant = variant_connection.nodes[0]
    product = variant.product
    if not product or not getattr(product, "id", None):
        logger.error(f"Product lookup for SKU '{sku}' returned no product id.")
        raise ValueError(f"Product lookup for SKU '{sku}' returned no product id.")

    return variant.product
