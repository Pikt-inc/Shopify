from pydantic import BaseModel, Field
import logging
from typing import Optional, TYPE_CHECKING, cast

from shopify_sdk.gql.core.types.base import ID
from shopify_sdk.gql.core.types.enums import ProductStatus
from .media import MediaManager
from .products_bulk import BulkProductManager as BulkProductManager
from .products_bulk import HandleScopePartition as HandleScopePartition
from .variants import ProductVariantManager

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from shopify_sdk.gql.core.types.payload import ProductUpdatePayload
    from shopify_sdk.gql.core.types.connections import ProductConnection
    from shopify_sdk.gql.core.types import MetafieldInput


class ProductManager(BaseModel):
    variants: ProductVariantManager = Field(default_factory=ProductVariantManager)
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

    @property
    def all(self) -> "ProductConnection":
        return self.query_all()

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

    def query_all(self, query: Optional[str] = None) -> "ProductConnection":
        """Retrieve products, optionally scoped by a Shopify query."""
        from shopify_sdk.gql.queries import products
        from shopify_sdk.gql.core.types.connections import ProductConnection

        product_query = products(
            query=query,
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
        response = cast(ProductConnection, product_query.bulk())
        return response
