from typing import List, Optional

from pydantic import BaseModel
from datetime import datetime


from .core import (
    ShopifyResource,
    ShopifyResourceFactory
)

class ProductVariant(ShopifyResource):
    title: str
    sku: Optional[str]
    barcode: Optional[str]
    price: Optional[str]
    compareAtPrice: Optional[str]
    inventoryQuantity: Optional[int]
    inventoryPolicy: Optional[str]
    requiresShipping: Optional[bool]
    weight: Optional[float]
    weightUnit: Optional[str]
    createdAt: datetime
    updatedAt: datetime

class ProductVariantFactory(ShopifyResourceFactory):
    _RESOURCE_TYPE = ProductVariant

@ProductVariantFactory.register_mutation(
    ShopifyResourceFactory.MutationType.RETRIEVE
)
def create_product_variant_mutation() -> str:
    return """
    query($identifier: ProductVariantIdentifierInput!) {
      productVariantByIdentifier(identifier: $identifier) {
        id
        title
        sku
        barcode
        price
        compareAtPrice
        inventoryQuantity
        inventoryPolicy
        requiresShipping
        weight
        weightUnit
        createdAt
        updatedAt
      }
    }
    """