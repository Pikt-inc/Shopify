import logging
from pydantic import BaseModel
from typing import Optional, cast
from typing import TYPE_CHECKING

from shopify_sdk.gql.queries import productVariants

if TYPE_CHECKING:
    from shopify_sdk.gql.core.types.connections import ProductVariantConnection


logger = logging.getLogger(__name__)


class ProductVariantManager(BaseModel):
    def query_all(self, query: Optional[str] = None) -> "ProductVariantConnection":
        """Retrieve product variants, optionally scoped by a Shopify query."""

        connection = productVariants(
            query=query,
            field_inclusions={
                "ProductVariant": {
                    "id",
                    "sku",
                    "price",
                    "inventoryQuantity",
                    "product",
                },
                "Product": {"id", "title"},
            },
        ).bulk()
        return cast("ProductVariantConnection", connection)

    @property
    def all(self) -> "ProductVariantConnection":
        """Retrieve all product variants."""
        return self.query_all()

    def get_variant_to_product_map(self, query: Optional[str] = None) -> dict[str, str]:
        """Return a mapping of variant IDs to their parent product IDs."""

        mapping: dict[str, str] = {}
        connection = self.query_all(query=query)
        for variant in connection.nodes:
            product = getattr(variant, "product", None)
            if (
                not product
                or not getattr(product, "id", None)
                or not getattr(variant, "id", None)
            ):
                logger.warning("Missing product or variant id for variant %s", variant)
                continue
            mapping[variant.id] = product.id
        return mapping

    @property
    def variant_to_product_map(self) -> dict[str, str]:
        return self.get_variant_to_product_map()

    def get_product_to_variants_map(
        self, query: Optional[str] = None
    ) -> dict[str, list[str]]:
        """Return a mapping of product IDs to their variant IDs."""

        mapping: dict[str, list[str]] = {}
        connection = self.query_all(query=query)
        for variant in connection.nodes:
            product = getattr(variant, "product", None)
            product_id = getattr(product, "id", None) if product else None
            variant_id = getattr(variant, "id", None)
            if not product_id or not variant_id:
                logger.warning("Missing product or variant id for variant %s", variant)
                continue
            if product_id not in mapping:
                mapping[product_id] = []
            mapping[product_id].append(variant_id)
        return mapping

    @property
    def product_to_variants_map(self) -> dict[str, list[str]]:
        return self.get_product_to_variants_map()

    def get_sku_to_variant_map(self, query: Optional[str] = None) -> dict[str, str]:
        """Return a mapping of SKUs to their variant IDs."""

        mapping: dict[str, str] = {}
        connection = self.query_all(query=query)
        for variant in connection.nodes:
            if variant.sku:
                mapping[variant.sku] = variant.id
        return mapping

    @property
    def sku_to_variant_map(self) -> dict[str, str]:
        return self.get_sku_to_variant_map()
