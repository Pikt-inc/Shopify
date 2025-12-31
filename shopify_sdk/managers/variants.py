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
