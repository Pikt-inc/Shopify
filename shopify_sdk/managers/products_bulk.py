from __future__ import annotations

import logging
from typing import NamedTuple, Optional, TYPE_CHECKING, Sequence, cast

from pydantic import BaseModel

from shopify_sdk.gql.core.types.base import ID
from shopify_sdk.gql.core.types.enums import ProductStatus

if TYPE_CHECKING:
    from shopify_sdk.gql.core.mutation import Mutation
    from shopify_sdk.gql.core.types import ProductCreateInput
    from shopify_sdk.gql.core.types import ProductSetInput
    from shopify_sdk.gql.core.types.payload import ProductSetPayload

logger = logging.getLogger(__name__)


class HandleScopePartition(NamedTuple):
    """Partition requested handles by whether they exist inside or outside a scope.

    `in_scope` contains handles present in the scoped query result.
    `out_of_scope` contains handles present in the store globally but absent from the
    scoped query result, which usually indicates a collision with unmanaged products.
    `missing` contains handles not found anywhere in the store.
    """

    in_scope: dict[str, ID]
    out_of_scope: dict[str, ID]
    missing: list[str]


class BulkProductManager(BaseModel):
    def create(self, products: Sequence["ProductCreateInput"]) -> list[ID]:
        from shopify_sdk.gql.mutations import productCreate

        if not products:
            return []

        mutations: list[Mutation] = []
        for input_data in products:
            mutations.append(
                productCreate(
                    product=input_data,
                    field_inclusions={
                        "ProductCreatePayload": {"product", "userErrors"},
                        "Product": {"id", "handle"},
                        "UserError": {"field", "message"},
                    },
                )
            )

        created_ids: list[ID] = []
        errors: list[str] = []
        for index, payload in enumerate(productCreate.bulk(mutations), start=1):
            user_errors = getattr(payload, "userErrors", []) or []
            if user_errors:
                messages = ", ".join(error.message for error in user_errors)
                errors.append(f"{index}: {messages}")
                continue
            product_obj = getattr(payload, "product", None)
            product_id = getattr(product_obj, "id", None)
            if not product_id:
                errors.append(f"{index}: no product id returned")
                continue
            created_ids.append(cast(ID, product_id))

        if errors:
            details = "; ".join(errors[:5])
            if len(errors) > 5:
                details = f"{details}; ... ({len(errors)} total failures)"
            raise ValueError(f"Bulk product creation failed: {details}")

        return created_ids

    def delete(self, ids: Sequence[ID]) -> list[ID]:
        from shopify_sdk.gql.core.types.input_objects import ProductDeleteInput
        from shopify_sdk.gql.mutations import productDelete

        if not ids:
            return []

        mutations: list[Mutation] = [
            productDelete(
                input=ProductDeleteInput(id=product_id),
                field_inclusions={
                    "ProductDeletePayload": {"deletedProductId", "userErrors"},
                    "UserError": {"field", "message"},
                },
            )
            for product_id in ids
        ]

        deleted_ids: list[ID] = []
        errors: list[str] = []
        for index, payload in enumerate(productDelete.bulk(mutations), start=1):
            user_errors = getattr(payload, "userErrors", []) or []
            if user_errors:
                messages = ", ".join(error.message for error in user_errors)
                errors.append(f"{index}: {messages}")
                continue
            deleted_id = getattr(payload, "deletedProductId", None)
            if not deleted_id:
                errors.append(f"{index}: no deleted product id returned")
                continue
            deleted_ids.append(cast(ID, deleted_id))

        if errors:
            details = "; ".join(errors[:5])
            if len(errors) > 5:
                details = f"{details}; ... ({len(errors)} total failures)"
            raise ValueError(f"Bulk product deletion failed: {details}")

        return deleted_ids

    def missing_skus(
        self,
        skus: list[str],
        query: Optional[str] = None,
    ) -> list[str]:
        """
        Return SKUs from the input list that do not exist in the scoped store set.
        """
        from shopify_sdk.gql.queries import productVariants

        connection = productVariants(
            query=query,
            field_inclusions={
                "ProductVariantConnection": {"edges"},
                "ProductVariant": {"sku"},
            }
        ).bulk()
        if hasattr(connection, "count") and connection.count == 0:
            return list(skus)
        if not hasattr(connection, "nodes"):
            raise ValueError("Failed to fetch product variants from store.")

        found_skus: set = set(
            [node.sku for node in connection.nodes if node.sku is not None]
        )

        diff = set(skus) - found_skus
        return list(diff)

    def missing_handles(
        self, handles: list[str], query: Optional[str] = None
    ) -> list[str]:
        """
        Return handles from the input list that do not exist in the scoped store set.

        When a scope query is provided, a handle may still exist elsewhere in the
        store but outside that scope. Use `partition_handles` when callers need to
        distinguish true absences from out-of-scope collisions.
        """
        from shopify_sdk.gql.queries import products

        connection = products(
            query=query,
            field_inclusions={
                "ProductConnection": {"edges"},
                "Product": {"handle"},
            }
        ).bulk()
        if hasattr(connection, "count") and connection.count == 0:
            return list(handles)
        if not hasattr(connection, "nodes"):
            raise ValueError("Failed to fetch products from store.")

        found_handles: set = set(
            [node.handle for node in connection.nodes if node.handle is not None]
        )

        diff = set(handles) - found_handles
        return list(diff)

    def partition_handles(
        self, handles: list[str], query: Optional[str] = None
    ) -> HandleScopePartition:
        """Partition handles into in-scope, out-of-scope, and globally missing.

        This is the safe helper to use for mixed-inventory stores where product
        handles are globally unique but only a scoped subset should be managed.
        """

        global_map = self.get_handle_id_map()
        scoped_map = global_map if query is None else self.get_handle_id_map(query=query)

        in_scope: dict[str, ID] = {}
        out_of_scope: dict[str, ID] = {}
        missing: list[str] = []

        for handle in handles:
            if handle in scoped_map:
                in_scope[handle] = scoped_map[handle]
            elif handle in global_map:
                out_of_scope[handle] = global_map[handle]
            else:
                missing.append(handle)

        return HandleScopePartition(
            in_scope=in_scope,
            out_of_scope=out_of_scope,
            missing=missing,
        )

    def partition_handles_by_tag(
        self, handles: list[str], tag: str
    ) -> HandleScopePartition:
        """Partition handles by a managed tag using a single full-store scan.

        This is the preferred helper for high-volume mixed-inventory workflows.
        It avoids the dual-query pattern of `partition_handles(..., query=...)` by
        scanning the store once for `handle`, `id`, and `tags`, then classifying
        only the requested handles in memory.
        """
        from shopify_sdk.gql.queries import products

        requested_handles = {handle for handle in handles if handle}
        if not requested_handles:
            return HandleScopePartition(in_scope={}, out_of_scope={}, missing=[])

        connection = products(
            field_inclusions={
                "ProductConnection": {"edges"},
                "Product": {"handle", "id", "tags"},
            }
        ).bulk()
        if not hasattr(connection, "nodes"):
            raise ValueError("Failed to fetch products from store.")

        in_scope: dict[str, ID] = {}
        out_of_scope: dict[str, ID] = {}
        found_handles: set[str] = set()

        for product in connection.nodes:
            handle = getattr(product, "handle", None)
            product_id = getattr(product, "id", None)
            if not handle or not product_id or handle not in requested_handles:
                continue

            found_handles.add(handle)
            tags = getattr(product, "tags", None) or []
            normalized_tags = {str(value) for value in tags if value}
            if tag in normalized_tags:
                in_scope[handle] = str(product_id)
            else:
                out_of_scope[handle] = str(product_id)

        missing = [handle for handle in handles if handle and handle not in found_handles]
        return HandleScopePartition(
            in_scope=in_scope,
            out_of_scope=out_of_scope,
            missing=missing,
        )

    def set(self, products: Sequence["ProductSetInput"]) -> list["ProductSetPayload"]:
        """
        Create or update products in bulk using productSet.
        Returns product IDs when available; when synchronous=False, falls back to operation IDs.
        """
        from shopify_sdk.gql.mutations import productSet

        if not products:
            return []

        mutations: list[Mutation] = []
        for input_data in products:
            mutations.append(
                productSet(
                    input=input_data,
                    synchronous=False,
                    field_inclusions={
                        "ProductSetOperation": {
                            "id",
                            "status",
                            "product",
                            "userErrors",
                        },
                        "Product": {"id"},
                        "ProductSetUserError": {"field", "message"},
                    },
                )
            )

        responses: list = []

        for payload in productSet.bulk(mutations):
            user_errors = getattr(payload, "userErrors", []) or []
            if user_errors != []:
                logger.error(f"ProductSet user errors: {user_errors}")
                raise ValueError("ProductSet operation returned user errors.")
            responses.append(payload)

        return responses

    def set_status(
        self,
        to_active: Optional[list[ID]] = None,
        to_archive: Optional[list[ID]] = None,
        to_draft: Optional[list[ID]] = None,
        fallback_status: Optional[ProductStatus] = ProductStatus.ARCHIVED,
        scope_query: Optional[str] = None,
    ) -> bool:
        """
        Set the status of products in the store, optionally scoped by query.
        Args:
            to_active (list[ID]): List of product IDs to set to active.
            to_archive (list[ID]): List of product IDs to set to archived.
            to_draft (list[ID]): List of product IDs to set to draft.
            fallback_status (ProductStatus): Fallback status for products not in the above lists.
            scope_query (str | None): Optional Shopify product query limiting the
                product universe used for validation and fallback status diffs.
        """
        from shopify_sdk.common.status_upsert import upsert_inventory_status

        if to_active is None:
            to_active = []
        if to_archive is None:
            to_archive = []
        if to_draft is None:
            to_draft = []
        return upsert_inventory_status(
            to_active=to_active,
            to_archive=to_archive,
            to_draft=to_draft,
            fallback_status=fallback_status,
            scope_query=scope_query,
        )

    def set_active_by_sku(
        self,
        skus: list[str],
        query: Optional[str] = None,
    ) -> bool:
        """
        Set products to active status based on a list of SKUs.
        This is an 'all or nothing' operation; all skus in the store will have their status updated.
        """
        from shopify_sdk.gql.queries import productVariants

        connection = productVariants(
            query=query,
            field_inclusions={
                "ProductVariantConnection": {"edges"},
                "ProductVariant": {"id", "sku", "product"},
                "Product": {"id"},
            }
        ).bulk()
        if hasattr(connection, "count") and connection.count == 0:
            logger.warning("No product variants found in store.")
            return False

        if not hasattr(connection, "nodes"):
            raise ValueError("Failed to fetch product variants from store.")

        pids = set()
        for variant in connection.nodes:
            if variant.sku in skus and variant.product and variant.product.id:
                pids.add(variant.product.id)

        return self.set_status(
            to_active=list(pids),
            fallback_status=ProductStatus.ARCHIVED,
            scope_query=query,
        )

    def publish(
        self,
        product_ids: list[ID],
    ) -> bool:
        """
        Publish products in bulk by setting their status to ACTIVE.
        """
        from shopify_sdk.gql.mutations import productPublish
        from shopify_sdk.gql.core.types.input_objects import (
            ProductPublishInput,
            ProductPublicationInput,
        )

        if not product_ids:
            raise ValueError("No product IDs provided for publishing.")

        from shopify_sdk.managers import store

        publication_connection = store.publications
        if publication_connection.count == 0:
            raise ValueError("No publications found in the store.")

        mutations: list["Mutation"] = []
        for product_id in product_ids:
            mutation = productPublish(
                input=ProductPublishInput(
                    id=product_id,
                    productPublications=[
                        ProductPublicationInput(publicationId=node.id)
                        for node in publication_connection.nodes
                    ],
                ),
                field_inclusions={"Product": {"id"}},
            )
            mutations.append(mutation)
        response = productPublish.bulk(mutations)
        for payload in response:
            user_errors = getattr(payload, "userErrors", []) or []
            if user_errors:
                messages = ", ".join(error.message for error in user_errors)
                raise ValueError(f"Product publishing failed: {messages}")
        return True

    def exchange(
        self,
        skus: list[str],
        query: Optional[str] = None,
    ) -> list[ID]:
        """
        Return product IDs for the given SKUs.
        """
        from shopify_sdk.managers import store

        pids: set[ID] = set()
        variant_connection = store.products.variants.query_all(query=query)
        for v in variant_connection.nodes:
            if not v.sku:
                logger.warning(
                    "No SKU found for product ID %s",
                    getattr(v.product, "id", "<unknown>"),
                )
                continue
            if not v.product or not v.product.id:
                logger.warning("No product found for variant with SKU %s", v.sku)
                continue
            if v.sku in skus:
                pids.add(str(v.product.id))
        return list(pids)

    def get_product_variant_map(
        self, query: Optional[str] = None
    ) -> dict[ID, list[ID]]:
        """
        Return a mapping of product IDs to their variant IDs.
        """
        from shopify_sdk.managers import store

        variants_manager = store.products.variants
        if query is None and not hasattr(variants_manager, "query_all"):
            pv_conn = variants_manager.all
        else:
            pv_conn = variants_manager.query_all(query=query)
        product_variant_map: dict[ID, list[ID]] = {}
        for variant in pv_conn.nodes:
            if not variant.product or not variant.product.id:
                logger.warning("No product found for variant ID %s", variant.id)
                continue
            product_id = str(variant.product.id)
            if product_id not in product_variant_map:
                product_variant_map[product_id] = []
            if variant.id:
                product_variant_map[product_id].append(str(variant.id))
        return product_variant_map

    @property
    def product_variant_map(self) -> dict[ID, list[ID]]:
        return self.get_product_variant_map()

    def get_handle_id_map(self, query: Optional[str] = None) -> dict[str, ID]:
        """
        Return a mapping of product handles to their IDs.
        """
        from shopify_sdk.managers import store

        products_manager = store.products
        if query is None and not hasattr(products_manager, "query_all"):
            product_conn = products_manager.all
        else:
            product_conn = products_manager.query_all(query=query)
        handle_id_map: dict[str, ID] = {}
        for product in product_conn.nodes:
            if not product.handle or not product.id:
                logger.warning("No handle or ID found for product.")
                continue
            handle_id_map[product.handle] = str(product.id)
        return handle_id_map

    @property
    def handle_id_map(self) -> dict[str, ID]:
        return self.get_handle_id_map()
