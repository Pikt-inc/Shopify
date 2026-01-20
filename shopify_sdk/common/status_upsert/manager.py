import logging
from functools import cached_property
from typing import Optional, Set, Iterator, cast

from shopify_sdk.gql.core.types import ID, Product, ProductStatus, ProductUpdateInput
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

    def __init__(self, input: InventorySyncInput) -> None:
        self._input: InventorySyncInput = input

    @cached_property
    def products(self) -> list[Product]:
        """
        Returns a list of all products in the store with their IDs and statuses.
        """
        from shopify_sdk.gql.core.types.connections import ProductConnection

        query = products(
            field_exclusions={
                "Product": Product.fields_except(exclude={"id", "status"})
            },
        )
        prod_connect = cast(ProductConnection, query.bulk())
        return prod_connect.nodes

    def _resolve_status_conflicts(
        self, input: InventorySyncInput
    ) -> InventorySyncInput:
        """
        Identify which product's have different statuses than those provided in the input.
        The goal of this function is to avoid unnecessary updates for products that already have the desired status.
        """
        resolved_active: Set[ID] = set()
        resolved_archived: Set[ID] = set()
        resolved_draft: Set[ID] = set()
        for pid in input.active:
            product = next((p for p in self.products if p.id == pid), None)
            if product and product.status != ProductStatus.ACTIVE:
                resolved_active.add(pid)
        for pid in input.archived:
            product = next((p for p in self.products if p.id == pid), None)
            if product and product.status != ProductStatus.ARCHIVED:
                resolved_archived.add(pid)
        for pid in input.draft:
            product = next((p for p in self.products if p.id == pid), None)
            if product and product.status != ProductStatus.DRAFT:
                resolved_draft.add(pid)
        return InventorySyncInput(
            active=list(resolved_active),
            archived=list(resolved_archived),
            draft=list(resolved_draft),
        )

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
        resolved_input = manager._resolve_status_conflicts(input)
        for status, id_list in [
            (ProductStatus.ACTIVE, resolved_input.active),
            (ProductStatus.ARCHIVED, resolved_input.archived),
            (ProductStatus.DRAFT, resolved_input.draft),
        ]:
            if not id_list:
                continue

            success = manager._bulk_set_status(status=status, id_list=id_list)
            if not success:
                logger.error(f"Failed to set status '{status}' for IDs: {id_list}")
                return False

        # Handle diff IDs (default to ARCHIVED)
        if manager.diff_ids:
            fallback = fallback_status or ProductStatus.ARCHIVED
            success = manager._bulk_set_status(
                status=fallback, id_list=list(manager.diff_ids)
            )
            if not success:
                logger.error(
                    f"Failed to set fallback status '{fallback}' for diff IDs: {manager.diff_ids}"
                )
                return False
        return True

    @cached_property
    def valid_ids(self) -> list[ID]:
        _ids = [product.id for product in self.products if product.id]
        return _ids

    @cached_property
    def diff_ids(self) -> Set[ID]:
        # Find all ids in the store that are not in any of the input lists
        merged = self._input.merged_ids(self._input.model_dump())
        if not merged:
            logger.warning(
                "No IDs provided in input; all store products will be considered diff."
            )
            raise ValueError(
                "No IDs provided in input; all store products will be considered diff."
            )

        if not self.valid_ids:
            logger.warning(
                "No valid product IDs found in store during diff calculation."
            )
            raise ValueError(
                "No valid product IDs found in store during diff calculation."
            )

        return set(self.valid_ids) - set(merged)

    def _bulk_set_status(self, status: ProductStatus, id_list: list[ID]) -> bool:
        if not id_list:
            return True

        mutations: list[Mutation] = []
        for product_id in id_list:
            mutations.append(
                productUpdate(
                    product=ProductUpdateInput(id=product_id, status=status),
                    field_exclusions={"Product": Product.fields_except(exclude={"id"})},
                )
            )

        from shopify_sdk.gql.core.types.payload import ProductUpdatePayload

        result = cast(Iterator[ProductUpdatePayload], productUpdate.bulk(mutations))
        has_errors = False
        for r in result:
            if r.userErrors:
                logger.error(
                    f"Errors encountered during bulk status update: {r.userErrors}"
                )
                has_errors = True
        return not has_errors
