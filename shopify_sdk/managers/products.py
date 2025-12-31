from pydantic import BaseModel, Field
import logging
from typing import Optional, TYPE_CHECKING, cast, Sequence

from shopify_sdk.gql.core.types.base import ID
from shopify_sdk.gql.core.types.enums import ProductStatus
from .media import MediaManager

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from shopify_sdk.gql.core.mutation import Mutation
    from shopify_sdk.gql.core.types.payload import ProductUpdatePayload
    from shopify_sdk.gql.core.types.connections import ProductConnection
    from shopify_sdk.gql.core.types import MetafieldInput
    from shopify_sdk.gql.core.types import ProductCreateInput
    from shopify_sdk.gql.core.types import ProductSetInput
    from shopify_sdk.gql.core.types.payload import ProductSetPayload


class BulkProductManager(BaseModel):
    def create(self, products: Sequence["ProductCreateInput"]) -> list[ID]:
        from shopify_sdk.gql.core.mutation import Mutation
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
        from shopify_sdk.gql.core.mutation import Mutation
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
    ) -> list[str]:
        """
        Return SKUs from the input list that do not exist in the store.
        """
        from shopify_sdk.gql.queries import productVariants

        connection = productVariants(
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
        print(f"Found SKUs in store: {len(found_skus)}")
        diff = set(skus) - found_skus
        return list(diff)

    def set(self, products: Sequence["ProductSetInput"]) -> list["ProductSetPayload"]:
        """
        Create or update products in bulk using productSet.
        Returns product IDs when available; when synchronous=False, falls back to operation IDs.
        """
        from shopify_sdk.gql.core.mutation import Mutation
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
                        "Product": {"id", "variants"},
                        "ProductVariant": {"id", "sku"},
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
    ) -> bool:
        """
        Set the status of all products in the store.
        Args:
            to_active (list[ID]): List of product IDs to set to active.
            to_archive (list[ID]): List of product IDs to set to archived.
            to_draft (list[ID]): List of product IDs to set to draft.
            fallback_status (ProductStatus): Fallback status for products not in the above lists.
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


class ProductManager(BaseModel):
    bulk: BulkProductManager = Field(default_factory=BulkProductManager)
    media: MediaManager = Field(default_factory=MediaManager)

    def create(
        self,
        title: str,
        handle: Optional[str] = None,
        status: ProductStatus = ProductStatus.DRAFT,
        tags: Optional[list[str]] = None,
        vendor: Optional[str] = None,
        product_type: Optional[str] = None,
        description_html: Optional[str] = None,
        images: Optional[list[str]] = None,
        metafields: Optional[list["MetafieldInput"]] = None,
    ) -> ID:
        from shopify_sdk import client
        from shopify_sdk.common.product.media import set_product_images
        from shopify_sdk.gql.core.types import ProductCreateInput
        from shopify_sdk.gql.mutations import productCreate

        input_data = ProductCreateInput(
            title=title,
            handle=handle,
            status=status,
            tags=tags or [],
            vendor=vendor,
            productType=product_type,
            descriptionHtml=description_html,
            metafields=metafields or [],
        )
        payload = productCreate(
            product=input_data,
            field_inclusions={
                "ProductCreatePayload": {"product", "userErrors"},
                "Product": {"id", "status", "handle"},
            },
        ).execute(client)
        if payload is None or payload.product is None or not payload.product.id:
            raise ValueError("Product creation failed; no product ID returned.")
        if payload.userErrors:
            messages = ", ".join(error.message for error in payload.userErrors)
            raise ValueError(f"Product creation failed: {messages}")
        if images is not None:
            set_product_images(product_id=payload.product.id, images=images)
        return cast(ID, payload.product.id)

    def delete(self, id: ID) -> bool:
        from shopify_sdk import client
        from shopify_sdk.gql.core.types.input_objects import ProductDeleteInput
        from shopify_sdk.gql.mutations import productDelete

        payload = productDelete(
            input=ProductDeleteInput(id=id),
            field_inclusions={
                "ProductDeletePayload": {"deletedProductId", "userErrors"},
                "UserError": {"field", "message"},
            },
        ).execute(client)
        if payload is None:
            raise ValueError("Product deletion failed; no payload returned.")
        user_errors = getattr(payload, "userErrors", []) or []
        if user_errors:
            messages = ", ".join(error.message for error in user_errors)
            raise ValueError(f"Product deletion failed: {messages}")
        deleted_id = getattr(payload, "deletedProductId", None)
        if not deleted_id:
            raise ValueError("Product deletion failed; no deleted product ID returned.")
        return True

    @property
    def archived(self) -> "ProductConnection":
        from shopify_sdk.gql.queries import products
        from shopify_sdk.gql.core.types.connections import ProductConnection

        query = products(
            query=f"status:{ProductStatus.ARCHIVED.value}",
            field_inclusions={
                "Product": set(
                    {
                        "status",
                        "id",
                        "title",
                        "tags",
                        "productType",
                        "seo",
                        "vendor",
                        "totalInventory",
                        "handle",
                        "description",
                        "descriptionHtml",
                    }
                )
            },
        )
        response = cast(ProductConnection, query.bulk())
        return response

    @property
    def active(self) -> "ProductConnection":
        from shopify_sdk.gql.queries import products
        from shopify_sdk.gql.core.types.connections import ProductConnection

        query = products(
            query=f"status:{ProductStatus.ACTIVE.value}",
            field_inclusions={
                "Product": set(
                    {
                        "status",
                        "id",
                        "title",
                        "tags",
                        "productType",
                        "seo",
                        "vendor",
                        "totalInventory",
                        "handle",
                        "description",
                        "descriptionHtml",
                    }
                )
            },
        )
        response = cast(ProductConnection, query.bulk())
        return response

    @property
    def draft(self) -> "ProductConnection":
        return self.drafted

    @property
    def drafted(self) -> "ProductConnection":
        from shopify_sdk.gql.queries import products
        from shopify_sdk.gql.core.types.connections import ProductConnection

        query = products(
            query=f"status:{ProductStatus.DRAFT.value}",
            field_inclusions={
                "Product": set(
                    {
                        "status",
                        "id",
                        "title",
                        "tags",
                        "productType",
                        "seo",
                        "vendor",
                        "totalInventory",
                        "handle",
                        "description",
                        "descriptionHtml",
                    }
                )
            },
        )
        response = cast(ProductConnection, query.bulk())
        return response

    def set_status(
        self, id: ID, status: ProductStatus
    ) -> Optional["ProductUpdatePayload"]:
        from shopify_sdk.gql.mutations import productUpdate
        from shopify_sdk.gql.core.types import ProductUpdateInput
        from shopify_sdk import client

        input_data = ProductUpdateInput(
            id=id,
            status=status,
        )
        result = productUpdate(
            product=input_data, field_inclusions={"Product": set({"status", "id"})}
        ).execute(client)
        return cast(Optional["ProductUpdatePayload"], result)

    def find_product_id(
        self,
        sku: Optional[str] = None,
        handle: Optional[str] = None,
    ) -> Optional[ID]:
        """
        Look up a product ID by SKU or handle.
        """
        from shopify_sdk.gql.queries import products
        from shopify_sdk import client
        from shopify_sdk.gql.core.types.connections import ProductConnection

        if not sku and not handle:
            raise ValueError("Either sku or handle must be provided.")

        terms = []
        if sku:
            terms.append(f"sku:{sku}")
        if handle:
            terms.append(f"handle:{handle}")
        query = products(
            first=1,
            query=" ".join(terms),
            field_inclusions={"Product": {"id"}},
        )
        response = query.execute(client)
        if response is None:
            return None
        product_connection = cast(ProductConnection, response)
        if not product_connection.nodes:
            return None
        return product_connection.nodes[0].id

    def exchange(
        self,
        sku: Optional[str] = None,
        handle: Optional[str] = None,
    ) -> Optional[ID]:
        return self.find_product_id(sku=sku, handle=handle)

    def first_variant_id(self, product_id: ID) -> ID:
        """
        Return the first variant ID for a product.
        """
        from shopify_sdk import client
        from shopify_sdk.gql.core.types import ProductIdentifierInput
        from shopify_sdk.gql.queries import productByIdentifier

        product = productByIdentifier(
            identifier=ProductIdentifierInput(id=product_id, handle=None),
            field_inclusions={
                "Product": {"variants"},
                "ProductVariantConnection": {"nodes"},
                "ProductVariant": {"id"},
            },
        ).execute(client)
        variants = getattr(getattr(product, "variants", None), "nodes", None) or []
        if not variants:
            raise ValueError(f"No variants found for product '{product_id}'.")
        variant_id = getattr(variants[0], "id", None)
        if not variant_id:
            raise ValueError(f"No variant id returned for product '{product_id}'.")
        return cast(ID, variant_id)
