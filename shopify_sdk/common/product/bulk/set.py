from __future__ import annotations

from typing import Iterable, List, Iterator, TYPE_CHECKING
from functools import cached_property
import logging

from shopify_sdk.common.store.locations import get_locations
from shopify_sdk.gql.mutations import productSet
from shopify_sdk.gql.core.types import (
    ProductSetInput,
    SEOInput,
    ProductVariantSetInput,
    VariantOptionValueInput,
    ProductSetInventoryInput,
    OptionValueSetInput,
    OptionSetInput
)

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from shopify_sdk.common import ProxyProduct

def execute_bulk_product_set(
    products: List[ProxyProduct]
) -> bool:

    return BulkProductSetter.execute(products=products)

class BulkProductSetter:
    """
    Manager class for handling bulk product creation.
    """

    def __init__(self, products: List[ProxyProduct]):
        self._products = products

    @cached_property
    def variables(self) -> list[ProductSetInput]:
        return self._cast_to_input(self._products)
    
    
    @classmethod
    def execute(
        cls,
        products: List[ProxyProduct]
    ) -> bool:
        creator = cls(products=products)
        res = productSet.bulk(
            mutations=[
                productSet(input=var) for var in creator.variables
            ]
        )
        for r in res:
            print(r)

    def _cast_to_input(self, product_list: Iterable[ProxyProduct]) -> list[dict]:
        lines: list[dict] = []
        for product in product_list:
            product_set_input = ProductSetInput(
                title=product.title,
                vendor=product.vendor,
                productType=product.type,
                tags=product.tags,
                descriptionHtml=product.description_html,
                seo=SEOInput(
                    title=product.seo_title,
                    description=product.seo_description,
                ),
                productOptions=[
                    OptionSetInput(
                        name="Title",
                        values=[
                            OptionValueSetInput(
                                name="Default Title"
                            )
                        ]
                    )
                ],
                variants=[
                    ProductVariantSetInput(
                        sku=product.sku,
                        price=product.price,
                        inventoryPolicy="DENY",
                        optionValues=[
                            VariantOptionValueInput(
                                optionName="Title",
                                name="Default Title"
                            )
                        ],
                        inventoryQuantities=[
                            ProductSetInventoryInput(
                                quantity=product.quantity,
                                locationId=location.id,
                                name='available'
                            ) for location in get_locations()
                        ]
                    )
                ]
            )
            if product.metafields:
                for mf in product.metafields:
                    product_set_input.metafields.append(
                        mf
                    )
            lines.append(product_set_input)
        return lines

