from __future__ import annotations

from typing import Iterable, List, Iterator, TYPE_CHECKING
from functools import cached_property
import logging

from shopify_sdk.tools import run_bulk_mutation
from shopify_sdk.tools.bulk import BulkOperationResult
from shopify_sdk.gql.mutations import productVariantsBulkCreate
from shopify_sdk.gql.core.types import (
    ProductVariantsBulkInput,
    InventoryItemInput,
    VariantOptionValueInput

)

logger = logging.getLogger(__name__)

PRODUCT_COUNT = 2

if TYPE_CHECKING:
    from shopify_sdk.common import ProxyProduct

def execute_bulk_variant_create(
    products: List[ProxyProduct]
) -> bool:
    for product in products:
        if not product.id:
            raise ValueError("Product ID must be set for bulk variant creation.")
        
    return BulkVariantCreator.execute(products=products)

class BulkVariantCreator:
    """
    Manager class for handling bulk product creation.
    """

    def __init__(self, products: List[ProxyProduct]):
        self._products = products

    @cached_property
    def variables(self) -> list[dict]:
        return self._cast_to_input(self._products)
    
    @classmethod
    def execute(
        cls,
        products: List[ProxyProduct]
    ) -> bool:
        creator = cls(products=products)
        results: Iterator[BulkOperationResult] = run_bulk_mutation(
            productVariantsBulkCreate, creator.variables, verbose=True
        )
        for index, result in enumerate(results):
            if result.user_errors or result.top_errors:
                logger.error(f"Product creation failed for line {result.line_number or index + 1}: {result.user_errors} {result.top_errors}")
                raise ValueError(f"Product creation failed for line {result.line_number or index + 1}")

        return True
            
    def _cast_to_input(self, product_list: Iterable[ProxyProduct]) -> list[dict]:
        lines: list[dict] = []
        for product in product_list:
            variant_input = ProductVariantsBulkInput(
                price=getattr(product, "price", None),
                inventoryItem=InventoryItemInput(
                    sku=product.sku,
                    tracked=True,
                    requiresShipping=True
                ),
                inventoryPolicy="DENY",
                taxable=True,
                optionValues=[
                    VariantOptionValueInput(
                        name="Title",
                        value="Default Title"
                    ).to_graphql()
                ]
            )
            # run_bulk_mutation expects each variables item to map mutation arg names to values
            lines.append({
                "productId": product.id,
                "variants": [variant_input.to_graphql()],
            })
        return lines

