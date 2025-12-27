from __future__ import annotations

from typing import Iterable, List, Iterator, TYPE_CHECKING
from functools import cached_property
import logging

from shopify_sdk.tools import run_bulk_mutation
from shopify_sdk.tools.bulk import BulkOperationResult
from shopify_sdk.gql.mutations import productUpdate
from shopify_sdk.gql.core.types import ProductUpdateInput, ProductStatus, SEOInput

logger = logging.getLogger(__name__)

PRODUCT_COUNT = 2

if TYPE_CHECKING:
    from shopify_sdk.common import ProxyProduct

def execute_bulk_product_update(
    products: List[ProxyProduct]
) -> bool:
    for _product in products:
        if not _product.id:
            logger.error("Each product must have an 'id' for bulk update.")
            raise ValueError("Each product must have an 'id' for bulk update.")
    return BulkProductUpdate.execute(products=products)

class BulkProductUpdate:
    """
    Manager class for handling bulk product creation.
    """

    @cached_property
    def variables(self) -> list[ProductUpdateInput]:
        return self._cast_to_input(self._products)
    
    @classmethod
    def execute(
        cls,
        products: List[ProxyProduct]
    ) -> bool:
        creator = cls(products=products)
        results: Iterator[BulkOperationResult] = run_bulk_mutation(
            productUpdate, creator.variables, verbose=True
        )

        for index, result in enumerate(results):
            if result.user_errors or result.top_errors:
                logger.error(f"Product creation failed for line {result.line_number or index + 1}: {result.user_errors} {result.top_errors}")
                raise ValueError(f"Product creation failed for line {result.line_number or index + 1}")

        return True
            
    def _cast_to_input(self, product_list: Iterable[ProxyProduct]) -> list[ProductUpdateInput]:
        lines: list[ProductUpdateInput] = []
        for product in product_list:
            seo = None
            if product.seo_title is not None or product.seo_description is not None:
                seo = SEOInput(
                    title=product.seo_title,
                    description=product.seo_description,
                )
            update_input = ProductUpdateInput(
                id=product.id,
                title=product.title,
                descriptionHtml=product.description_html,
                vendor=product.vendor,
                productType=product.type,
                tags=product.tags or [],
                status=ProductStatus.ACTIVE,
                seo=seo,
                metafields=product.metafields,
            )
            lines.append(update_input)
        return lines

