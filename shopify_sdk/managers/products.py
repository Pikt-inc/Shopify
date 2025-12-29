from pydantic import BaseModel, Field
from typing import List, Optional, TYPE_CHECKING, cast

from shopify_sdk.gql.core.types.base import ID
from shopify_sdk.gql.core.types.enums import ProductStatus
from shopify_sdk.gql.core.types.objects import Product

if TYPE_CHECKING:
    from shopify_sdk.gql.core.types.payload import ProductUpdatePayload

class BulkProductManager(BaseModel):

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


class ProductManager(BaseModel):
    bulk: BulkProductManager = Field(default_factory=BulkProductManager)
    
    @property
    def archived(self) -> List[Product]:
        from shopify_sdk.gql.queries import products
        from shopify_sdk.gql.core.types.connections import ProductConnection
        query = products(
            query=f"status:{ProductStatus.ARCHIVED.value}",
            field_inclusions={
                "Product": set(
                    {
                        "status", "id", "title", "tags",
                        "productType", "seo", "vendor",
                        "totalInventory", "handle", "description",
                        "descriptionHtml"
                    }
                )
            },
        )
        response = cast(ProductConnection, query.bulk())
        return response.nodes
    
    @property
    def active(self) -> List[Product]:
        from shopify_sdk.gql.queries import products
        from shopify_sdk.gql.core.types.connections import ProductConnection
        query = products(
            query=f"status:{ProductStatus.ACTIVE.value}",
            field_inclusions={
                "Product": set(
                    {
                        "status", "id", "title", "tags",
                        "productType", "seo", "vendor",
                        "totalInventory", "handle", "description",
                        "descriptionHtml"
                    }
                )
            },
        )
        response = cast(ProductConnection, query.bulk())
        return response.nodes

    @property
    def draft(self) -> List[Product]:
        return self.drafted

    @property
    def drafted(self) -> List[Product]:
        from shopify_sdk.gql.queries import products
        from shopify_sdk.gql.core.types.connections import ProductConnection
        query = products(
            query=f"status:{ProductStatus.DRAFT.value}",
            field_inclusions={
                "Product": set(
                    {
                        "status", "id", "title", "tags",
                        "productType", "seo", "vendor",
                        "totalInventory", "handle", "description",
                        "descriptionHtml"
                    }
                )
            },
        )
        response = cast(ProductConnection, query.bulk())
        return response.nodes

    def set_status(self, id: ID, status: ProductStatus) -> Optional["ProductUpdatePayload"]:
        from shopify_sdk.gql.mutations import productUpdate
        from shopify_sdk.gql.core.types import ProductUpdateInput
        from shopify_sdk import client
        input_data = ProductUpdateInput(
            id=id,
            status=status,
        )
        result = productUpdate(
            product=input_data,
            field_inclusions={
                "Product": set(
                    {
                        "status", "id"
                    }
                )
            }
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
            field_inclusions={
                "Product": {"id"}
            },
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
        
