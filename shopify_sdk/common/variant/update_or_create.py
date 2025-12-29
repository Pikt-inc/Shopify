from functools import cached_property

from shopify_sdk.gql.core.types import ProductVariant, ProductVariantsBulkInput, ID
from shopify_sdk.gql.core.types.input_objects import InventoryItemInput
from shopify_sdk.gql.core.types.enums import ProductVariantInventoryPolicy
from shopify_sdk.gql.mutations import (
    productVariantsBulkUpdate,
    productVariantsBulkCreate,
)
from shopify_sdk import client


def update_variant(
    product_id: str,
    variant_update_input: ProductVariantsBulkInput,
) -> bool:
    success = False
    result = productVariantsBulkUpdate(
        productId=product_id,
        variants=[variant_update_input],
    ).execute(client=client)
    if result and result.get("userErrors") == []:
        success = True
    return success


def create_variant(
    product_id: str,
    variant_create_input: ProductVariantsBulkInput,
) -> bool:
    success = False
    result = productVariantsBulkCreate(
        productId=product_id,
        variants=[variant_create_input],
    ).execute(client=client)
    if result and result.get("userErrors") == []:
        success = True
    return success


def update_or_create_variant(variant: ProductVariant, product_id: str) -> bool:
    """
    Update an existing product variant or create a new one if it does not exist.
    """
    return UpdateOrCreateVariant(variant=variant, product_id=product_id).execute()


class UpdateOrCreateVariant:
    def __init__(self, variant: ProductVariant, product_id: ID):
        self._variant = variant
        self._product_id = product_id

    @cached_property
    def variant_exists(self) -> bool:
        if not self.variant.id:
            return False
        return True

    @cached_property
    def variant(self) -> ProductVariant:
        return self._variant

    @cached_property
    def variant_create_input(self) -> ProductVariantsBulkInput:
        return self._build_bulk_input(include_id=False)

    @cached_property
    def variant_update_input(self) -> ProductVariantsBulkInput:
        return self._build_bulk_input(include_id=True)

    def _build_bulk_input(self, include_id: bool) -> ProductVariantsBulkInput:
        inventory_item = getattr(self.variant, "inventoryItem", None)
        inventory_item_input = None
        if inventory_item:
            inventory_item_input = InventoryItemInput(
                sku=inventory_item.sku,
                tracked=inventory_item.tracked,
                requiresShipping=inventory_item.requiresShipping,
            )

        return ProductVariantsBulkInput(
            id=self.variant.id if include_id else None,
            price=getattr(self.variant, "price", None),
            compareAtPrice=getattr(self.variant, "compareAtPrice", None),
            barcode=self.variant.barcode,
            inventoryPolicy=getattr(
                self.variant,
                "inventoryPolicy",
                ProductVariantInventoryPolicy.DENY,
            ),
            inventoryItem=inventory_item_input,
        )

    def _update_variant(self) -> bool:
        success = False
        result = productVariantsBulkUpdate(
            productId=self._product_id,
            variants=[self.variant_update_input],
        ).execute(client=client)
        if result and result.get("userErrors") == []:
            success = True
        return success

    def _create_variant(self) -> bool:
        success = False
        result = productVariantsBulkCreate(
            productId=self._product_id,
            variants=[self.variant_create_input],
        ).execute(client=client)
        if result and result.get("userErrors") == []:
            success = True
        return success

    def execute(self) -> bool:
        if self.variant_exists:
            return self._update_variant()
        else:
            return self._create_variant()
