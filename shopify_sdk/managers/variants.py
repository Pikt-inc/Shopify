import logging
from pydantic import BaseModel
from typing import cast
from typing import TYPE_CHECKING

from shopify_sdk.gql.queries import productVariants

if TYPE_CHECKING:
    from shopify_sdk.gql.core.types.connections import ProductVariantConnection


logger = logging.getLogger(__name__)


class ProductVariantManager(BaseModel):
    @property
    def all(self) -> "ProductVariantConnection":
        """Retrieve all product variants."""
        connection = productVariants(
            field_inclusions={
                "ProductVariant": {
                    "id",
                    "sku",
                    "price",
                    "inventoryQuantity",
                    "product",
                },
                "Product": {"id", "title"},
            }
        ).bulk()
        return cast("ProductVariantConnection", connection)

    @property
    def variant_to_product_map(self) -> dict[str, str]:
        """Return a mapping of variant IDs to their parent product IDs."""
        mapping: dict[str, str] = {}
        connection = self.all
        for variant in connection.nodes:
            if variant.sku:
                mapping[variant.sku] = variant.product.id
        return mapping

    @property
    def product_to_variants_map(self) -> dict[str, list[str]]:
        """Return a mapping of product IDs to their variant IDs."""
        mapping: dict[str, list[str]] = {}
        connection = self.all
        for variant in connection.nodes:
            product_id = variant.product.id
            if product_id not in mapping:
                mapping[product_id] = []
            mapping[product_id].append(variant.id)
        return mapping

    @property
    def sku_to_variant_map(self) -> dict[str, str]:
        """Return a mapping of SKUs to their variant IDs."""
        mapping: dict[str, str] = {}
        connection = self.all
        for variant in connection.nodes:
            if variant.sku:
                mapping[variant.sku] = variant.id
        return mapping
