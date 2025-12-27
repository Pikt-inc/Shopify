import logging
from functools import cached_property
from typing import Optional, Set

from shopify_sdk.gql.core.types import (
    ID, Product, ProductStatus, ProductUpdateInput
)
from shopify_sdk.gql.queries import products
from shopify_sdk.gql.mutations import productUpdate
from shopify_sdk.tools.bulk import run_bulk_query, run_bulk_mutation

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

            success = manager._bulk_set_status(
                status=status,
                id_list=id_list
            )

            if not success:
                logger.error(f"Failed to set status '{status}' for IDs: {id_list}")
                raise ValueError(f"Failed to set status '{status}' for IDs: {id_list}")
            
        # Handle diff IDs if a fallback status is provided
        if manager.diff_ids and fallback_status is not None:
            fallback = fallback_status
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
        bulk_query = products(
            field_exclusions={
                "Product": Product.fields_except(
                    exclude={"id"}
                )
            }
        )
        _ids: list[ID] = []
        for line in run_bulk_query(bulk_query, verbose=True):
            product_id = line.get('id', None)
            if not product_id:
                logger.warning("Encountered product with no ID during validation.")
                raise ValueError("Encountered product with no ID during validation.")
            _ids.append(product_id)
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

        variables: list[ProductUpdateInput] = []
        for product_id in id_list:
            mutation_input = ProductUpdateInput(
                id=product_id,
                status=status
            )
            variables.append(mutation_input)
            
        result = run_bulk_mutation(
            action=productUpdate,
            variables_iter=variables,
            verbose=True
        )
        for res in result:
            if res.user_errors or res.top_errors:
                logger.error(f"Failed to update product ID in bulk mutation: {res.user_errors} {res.top_errors}")
                return False
        return True

