from __future__ import annotations
from functools import cached_property
from typing import cast

from shopify_sdk.common.store.locations import get_locations
from shopify_sdk.common.store.inventory import update_inventory
from shopify_sdk.common.product.query import (
    variants_by_product
)
from shopify_sdk.common.product.publish import (
    publish_product_to_all_publications
)
from shopify_sdk.common.variant.update_or_create import update_variant
from shopify_sdk.common.product.create import create_product

from shopify_sdk.gql.core.types import *
from shopify_sdk.gql.core.types.input_objects import *
from shopify_sdk.gql.core.types.enums import *
from shopify_sdk.gql.core.types.objects import *
from shopify_sdk.gql.core.types.connections import *
from .types import ProxyProduct

def update_product(
    product: ProxyProduct
) -> str:
    try:
        pc = ProductCreate.execute(
            proxy_product=product
        )
        return pc.product_id
    except Exception as e:
        raise ValueError(f"Product update or creation failed: {e}")


class ProductCreate:
    DEFAULT_LOCATION_NAME = "Shop location"

    def __init__(
        self,
        proxy_product: ProxyProduct
    ):
        self._proxy_product = proxy_product

    @cached_property
    def shop_location_id(self) -> ID:
        locations = get_locations()
        if locations.count == 0:
            raise ValueError("No shop locations found.")
        for location in locations:
            if location.name == self.DEFAULT_LOCATION_NAME:
                return ID(str(location.id))
        raise ValueError(f"Location with name '{self.DEFAULT_LOCATION_NAME}' not found.")
        

    @cached_property
    def product_id(self) -> str:
        return self._get_product_id()
    
    @cached_property
    def variant(self) -> ProductVariant:
        variant_connection = variants_by_product(
            product_id=self.product_id
        )
        if not variant_connection or not variant_connection.nodes:
            raise ValueError(f"No variants found for product ID '{self.product_id}'.")
        variant = variant_connection.first
        if variant is None:
            raise ValueError(f"No variants found for product ID '{self.product_id}'.")
        return cast(ProductVariant, variant)


    @cached_property
    def _get_product_create_input(self) -> ProductCreateInput:
        return ProductCreateInput(
            title=self._proxy_product.title,
            descriptionHtml=self._proxy_product.description_html,
            vendor=self._proxy_product.vendor,
            productType=self._proxy_product.type,
            tags=self._proxy_product.tags or [],
            status=ProductStatus.ACTIVE,
            seo=SEOInput(
                title=self._proxy_product.seo_title,
                description=self._proxy_product.seo_description
            )
        )

    @cached_property
    def _get_variant_create_input(self) -> ProductVariantsBulkInput:
        return ProductVariantsBulkInput(
            id=self.variant.id,
            price=self._proxy_product.price,
            inventoryPolicy=ProductVariantInventoryPolicy.DENY,
            inventoryItem=InventoryItemInput(
                sku=self._proxy_product.sku,
                tracked=True,
                requiresShipping=True
            )
        )
    
    @classmethod
    def execute(
        cls,
        proxy_product: ProxyProduct
    ) -> "ProductCreate":
        instance = cls(
            proxy_product=proxy_product
        )
        instance._set_variant()
        instance._set_inventory()
        publish_product_to_all_publications(
            product_id=instance.product_id
        )
        return instance

    def _set_variant(self) -> bool:
        success = update_variant(
            product_id=self.product_id,
            variant_update_input=self._get_variant_create_input
        )
        if not success:
            raise ValueError("Variant update failed.")
        return success
    
    def _get_product_id(self) -> str:
        return self._set_product()
    
    def _set_product(self) -> str:
        product_id = create_product(
            input=self._get_product_create_input
        )
        if not product_id:
            raise ValueError("Product creation failed.")
        return product_id

    def _set_inventory(self) -> bool:
        success = update_inventory(
            input=InventoryAdjustQuantitiesInput(
                name="available",
                reason="correction",
                changes=[
                    InventoryChangeInput(
                        inventoryItemId=self.variant.inventoryItem.id,
                        locationId=self.shop_location_id,
                        delta=int(self._proxy_product.quantity if self._proxy_product.quantity is not None else 0)
                    )
                ]
            )
        )
        if not success:
            raise ValueError("Inventory update failed.")
        return True
