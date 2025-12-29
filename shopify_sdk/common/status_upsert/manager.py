import logging
from functools import cached_property
from typing import Optional, Set, Iterator, cast

from shopify_sdk.gql.core.types import (
    ID, Product, ProductStatus, ProductUpdateInput
)
from shopify_sdk.gql.queries import products
from shopify_sdk.gql.mutations import productUpdate
from shopify_sdk.gql.core import Mutation

from .input import InventorySyncInput

logger = logging.getLogger(__name__)

class StatusUpsertManager:
    """
    Manager class for handling product upsert operations.

    DOES NOT UPDATE OR MODIFY PRODUCT DETAILS OTHER THAN STATUS.
    """

    def __init__(
        self,
        input: InventorySyncInput
    ) -> None:
        self._input: InventorySyncInput = input

    @classmethod
    def inventory_status_sync(
        cls,
        to_active: Optional[list[ID]] = None,
        to_archive: Optional[list[ID]] = None,
        to_draft: Optional[list[ID]] = None,
        fallback_status: Optional[ProductStatus] = ProductStatus.ARCHIVED,
    ) -> bool:
        if to_active is None:
            to_active = []
        if to_archive is None:
            to_archive = []
        if to_draft is None:
            to_draft = []
        input = InventorySyncInput(
            active=to_active,
            archived=to_archive,
            draft=to_draft,
        )
        manager = cls(input=input)
        for status, id_list in [
            (ProductStatus.ACTIVE, input.active),
            (ProductStatus.ARCHIVED, input.archived),
            (ProductStatus.DRAFT, input.draft),
        ]:
            if not id_list:
                continue

            manager._bulk_set_status(
                status=status,
                id_list=id_list
            )

        # Handle diff IDs (default to ARCHIVED)
        if manager.diff_ids:
            fallback = fallback_status or ProductStatus.ARCHIVED
            success = manager._bulk_set_status(
                status=fallback,
                id_list=list(manager.diff_ids)
            )
            if not success:
                logger.error(f"Failed to set fallback status '{fallback}' for diff IDs: {manager.diff_ids}")
                return False
        return True
        
    @cached_property
    def valid_ids(self) -> list[ID]:
        from shopify_sdk.gql.core.types.connections import ProductConnection
        query = products(
            field_exclusions={
                "Product": Product.fields_except(
                    exclude={"id"}
                )
            }
        )
        _ids: list[ID] = []
        prod_connect = cast(ProductConnection, query.bulk())
        if not prod_connect.nodes:
            logger.warning("No products found in store during validation of valid IDs.")
            raise ValueError("No products found in store during validation of valid IDs.")
        _ids = [product.id for product in prod_connect.nodes if product.id]
        return _ids
    
    @cached_property
    def diff_ids(self) -> Set[ID]:
        # Find all ids in the store that are not in any of the input lists
        merged = self._input.merged_ids(self._input.model_dump())
        if not merged:
            logger.warning("No IDs provided in input; all store products will be considered diff.")
            raise ValueError("No IDs provided in input; all store products will be considered diff.")
        
        if not self.valid_ids:
            logger.warning("No valid product IDs found in store during diff calculation.")
            raise ValueError("No valid product IDs found in store during diff calculation.")
        
        return set(self.valid_ids) - set(merged)
    
    def _bulk_set_status(
        self,
        status: ProductStatus,
        id_list: list[ID]
    ) -> bool:
        if not id_list:
            return True
        
        mutations: list[Mutation] = []
        for product_id in id_list:
            mutations.append(
                productUpdate(
                    product = ProductUpdateInput(
                        id=product_id,
                        status=status
                    ),
                    field_exclusions={
                        "Product": Product.fields_except(
                            exclude={"id"}
                        )
                    }
                )
            )
            
        from shopify_sdk.gql.core.types.payload import ProductUpdatePayload
        result = cast(Iterator[ProductUpdatePayload], productUpdate.bulk(mutations))
        for r in result:
            if r.userErrors:
                logger.error(f"Errors encountered during bulk status update: {r.userErrors}")
        return True
