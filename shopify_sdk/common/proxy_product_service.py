from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, cast

from shopify_sdk.common.product.create import (
    create_product as create_product_mutation,
)
from shopify_sdk.common.product.create import (
    update_product as update_product_mutation,
)
from shopify_sdk.common.product.media import set_product_images
from shopify_sdk.common.product.publish import publish_product_to_all_publications
from shopify_sdk.common.product.query import variants_by_product
from shopify_sdk.common.store.inventory import update_inventory
from shopify_sdk.common.store.locations import get_locations
from shopify_sdk.common.variant.update_or_create import update_variant
from shopify_sdk.gql.core.types import ID
from shopify_sdk.gql.core.types.enums import ProductStatus
from shopify_sdk.gql.core.types.enums import ProductVariantInventoryPolicy
from shopify_sdk.gql.core.types.input_objects import InventoryAdjustQuantitiesInput
from shopify_sdk.gql.core.types.input_objects import InventoryChangeInput
from shopify_sdk.gql.core.types.input_objects import InventoryItemInput
from shopify_sdk.gql.core.types.input_objects import ProductCreateInput
from shopify_sdk.gql.core.types.input_objects import ProductUpdateInput
from shopify_sdk.gql.core.types.input_objects import ProductVariantsBulkInput
from shopify_sdk.gql.core.types.input_objects import SEOInput
from shopify_sdk.gql.core.types.objects import ProductVariant

if TYPE_CHECKING:
    from shopify_sdk.common.types import ProxyProduct


def calculate_inventory_delta(
    desired_quantity: int | None,
    current_quantity: int | None,
) -> int:
    """Return the inventory delta needed to reach the desired quantity.

    :param desired_quantity: Requested inventory quantity.
    :param current_quantity: Current Shopify inventory quantity.
    :returns: Quantity adjustment delta for Shopify inventory APIs.
    """
    if desired_quantity is None:
        return 0
    return int(desired_quantity) - int(current_quantity or 0)


class ProxyProductWorkflow:
    """Shared orchestration for creating or updating a proxy product."""

    DEFAULT_LOCATION_NAME = "Shop location"

    def __init__(self, proxy_product: ProxyProduct) -> None:
        """Initialize the workflow for a proxy product.

        :param proxy_product: Product-like DTO used by legacy helpers.
        """
        self._proxy_product = proxy_product

    @cached_property
    def shop_location_id(self) -> ID:
        """Return the Shopify location ID used for inventory adjustments."""
        locations = get_locations()
        if locations.count == 0:
            raise ValueError("No shop locations found.")
        for location in locations:
            if location.name == self.DEFAULT_LOCATION_NAME:
                return ID(str(location.id))
        raise ValueError(
            f"Location with name '{self.DEFAULT_LOCATION_NAME}' not found."
        )

    @cached_property
    def variant(self) -> ProductVariant:
        """Return the first variant for the workflow product."""
        variant_connection = variants_by_product(product_id=self.product_id)
        if not variant_connection or not variant_connection.nodes:
            raise ValueError(f"No variants found for product ID '{self.product_id}'.")
        variant = variant_connection.first
        if variant is None:
            raise ValueError(f"No variants found for product ID '{self.product_id}'.")
        return cast(ProductVariant, variant)

    @cached_property
    def variant_input(self) -> ProductVariantsBulkInput:
        """Return the variant input shared by create and update workflows."""
        return ProductVariantsBulkInput(
            id=self.variant.id,
            price=self._proxy_product.price,
            inventoryPolicy=ProductVariantInventoryPolicy.DENY,
            inventoryItem=InventoryItemInput(
                sku=self._proxy_product.sku,
                tracked=True,
                requiresShipping=True,
            ),
        )

    @cached_property
    def product_id(self) -> str:
        """Return the Shopify product ID for the workflow."""
        raise NotImplementedError

    def apply_post_product_updates(self) -> None:
        """Apply variant, inventory, images, and publication updates."""
        self._set_variant()
        self._set_inventory()
        self._set_images()
        publish_product_to_all_publications(product_id=self.product_id)

    def _set_variant(self) -> bool:
        """Update the first product variant from proxy product fields."""
        success = update_variant(
            product_id=self.product_id,
            variant_update_input=self.variant_input,
        )
        if not success:
            raise ValueError("Variant update failed.")
        return success

    def _set_inventory(self) -> bool:
        """Adjust inventory quantity when the proxy product requests a change."""
        delta = calculate_inventory_delta(
            desired_quantity=self._proxy_product.quantity,
            current_quantity=self.variant.inventoryQuantity,
        )
        if delta == 0:
            return True
        return self._update_inventory(delta)

    def _update_inventory(self, delta: int) -> bool:
        """Send an inventory adjustment for the workflow variant."""
        success = update_inventory(input=self._inventory_input(delta))
        if not success:
            raise ValueError("Inventory update failed.")
        return True

    def _inventory_input(self, delta: int) -> InventoryAdjustQuantitiesInput:
        """Build the Shopify inventory adjustment input for a delta."""
        return InventoryAdjustQuantitiesInput(
            name="available",
            reason="correction",
            changes=[
                InventoryChangeInput(
                    inventoryItemId=self.variant.inventoryItem.id,
                    locationId=self.shop_location_id,
                    delta=delta,
                )
            ],
        )

    def _set_images(self) -> bool:
        """Replace product images when proxy image input is provided."""
        return set_product_images(self.product_id, self._proxy_product.images)


class ProductCreateWorkflow(ProxyProductWorkflow):
    """Create a Shopify product from a proxy product, then reconcile details."""

    @cached_property
    def product_id(self) -> str:
        """Return the created Shopify product ID."""
        return self._set_product()

    @cached_property
    def product_input(self) -> ProductCreateInput:
        """Return the Shopify product create input for the proxy product."""
        return ProductCreateInput(
            title=self._proxy_product.title,
            descriptionHtml=self._proxy_product.description_html,
            vendor=self._proxy_product.vendor,
            productType=self._proxy_product.type,
            tags=self._proxy_product.tags or [],
            status=ProductStatus.ACTIVE,
            seo=SEOInput(
                title=self._proxy_product.seo_title,
                description=self._proxy_product.seo_description,
            ),
            metafields=self._proxy_product.metafields,
        )

    @classmethod
    def execute(cls, proxy_product: ProxyProduct) -> ProductCreateWorkflow:
        """Create a product and apply proxy product follow-up updates."""
        instance = cls(proxy_product=proxy_product)
        instance.apply_post_product_updates()
        return instance

    def _set_product(self) -> str:
        """Create the Shopify product and return its ID."""
        product_id = create_product_mutation(input=self.product_input)
        if not product_id:
            raise ValueError("Product creation failed.")
        return product_id


class ProductUpdateWorkflow(ProxyProductWorkflow):
    """Update an existing Shopify product from a proxy product."""

    @cached_property
    def product_id(self) -> str:
        """Return the existing Shopify product ID being updated."""
        if not self._proxy_product.id:
            raise ValueError("Product ID is required for update.")
        return str(self._proxy_product.id)

    @cached_property
    def product_input(self) -> ProductUpdateInput:
        """Return the Shopify product update input for the proxy product."""
        return ProductUpdateInput(
            id=self.product_id,
            title=self._proxy_product.title,
            descriptionHtml=self._proxy_product.description_html,
            vendor=self._proxy_product.vendor,
            productType=self._proxy_product.type,
            tags=self._proxy_product.tags or [],
            status=ProductStatus.ACTIVE,
            seo=SEOInput(
                title=self._proxy_product.seo_title,
                description=self._proxy_product.seo_description,
            ),
            metafields=self._proxy_product.metafields,
        )

    @classmethod
    def execute(cls, proxy_product: ProxyProduct) -> ProductUpdateWorkflow:
        """Update a product and apply proxy product follow-up updates."""
        instance = cls(proxy_product=proxy_product)
        instance._update_product()
        instance.apply_post_product_updates()
        return instance

    def _update_product(self) -> str:
        """Update the Shopify product and refresh the proxy product ID."""
        product_id = update_product_mutation(input=self.product_input)
        if not product_id:
            raise ValueError("Product update failed.")
        self._proxy_product.id = product_id
        return product_id
