from __future__ import annotations

from typing import Iterable, List, Iterator, TYPE_CHECKING
from functools import cached_property
import logging

from shopify_sdk.tools import run_bulk_mutation
from shopify_sdk.tools.bulk import BulkOperationResult
from shopify_sdk.gql.mutations import productCreate
from shopify_sdk.gql.core.types import (
    ProductCreateInput, ProductStatus, SEOInput
)

logger = logging.getLogger(__name__)

PRODUCT_COUNT = 2

if TYPE_CHECKING:
    from shopify_sdk.common import ProxyProduct

def execute_bulk_product_create(
    products: List[ProxyProduct]
) -> bool:
    return BulkProductCreator.execute(products=products)

class BulkProductCreator:
    """
    Manager class for handling bulk product creation.
    """

    def __init__(self, products: List[ProxyProduct]):
        self._products = products

    @cached_property
    def variables(self) -> list[ProductCreateInput]:
        return self._cast_to_input(self._products)
    
    @classmethod
    def execute(
        cls,
        products: List[ProxyProduct]
    ) -> bool:
        creator = cls(products=products)
        results: Iterator[BulkOperationResult] = run_bulk_mutation(
            productCreate, creator.variables, verbose=True
        )
        for stream_index, result in enumerate(results, start=1):
            if result.line_number is not None:
                target_idx = result.line_number
                target_line = result.line_number
            else:
                target_line = stream_index
                target_idx = stream_index - 1
            if target_idx < 0 or target_idx >= len(products):
                logger.error(
                    "Bulk result line number out of range: %s (products=%s)",
                    target_line,
                    len(products),
                )
                raise IndexError(f"Bulk result line number out of range: {target_line}")
            product = products[target_idx]
            if result.user_errors or result.top_errors:
                logger.error(
                    f"Product creation failed for line {target_line}: {result.user_errors} {result.top_errors}"
                )
                raise ValueError(f"Product creation failed for line {target_line}")
            if result.payload:
                product.id = result.payload.get('product', {}).get('id')
        return True
            
    def _cast_to_input(self, product_list: Iterable[ProxyProduct]) -> list[ProductCreateInput]:
        lines: list[ProductCreateInput] = []
        for product in product_list:
            seo = None
            if product.seo_title is not None or product.seo_description is not None:
                seo = SEOInput(
                    title=product.seo_title,
                    description=product.seo_description,
                )
            create_input = ProductCreateInput(
                title=product.title,
                descriptionHtml=product.description_html,
                vendor=product.vendor,
                productType=product.type,
                tags=product.tags or [],
                status=ProductStatus.ACTIVE,
                seo=seo,
                metafields=product.metafields,
            )
            lines.append(create_input)
        return lines

