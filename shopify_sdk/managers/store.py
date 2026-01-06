import os
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator, Optional
from pydantic import BaseModel, Field

from .products import ProductManager
from .orders import OrderManager
from .delivery import DeliveryManager

if TYPE_CHECKING:
    from shopify_sdk.gql.core.types.connections import (
        LocationConnection,
        PublicationConnection,
    )
    from shopify_sdk.gql.core.types.base import ID


class StoreManager(BaseModel):
    products: ProductManager = Field(default_factory=ProductManager)
    orders: OrderManager = Field(default_factory=OrderManager)
    delivery: DeliveryManager = Field(default_factory=DeliveryManager)
    model_config = {
        "arbitrary_types_allowed": True,
    }

    @contextmanager
    def credentials_context(
        self,
        shop_domain: str,
        access_token: str,
        api_version: Optional[str] = None,
    ) -> Iterator["StoreManager"]:
        from shopify_sdk import client_context

        version = api_version or os.getenv("SHOPIFY_API_VERSION") or "2025-10"
        with client_context(
            shop_domain=shop_domain,
            access_token=access_token,
            api_version=version,
        ):
            yield self

    @property
    def locations(self) -> "LocationConnection":
        from shopify_sdk import client
        from shopify_sdk.gql.queries import locations

        query = locations(
            field_inclusions={
                "Location": set(
                    {
                        "id",
                        "name",
                        "address",
                        "city",
                        "country",
                        "province",
                        "zip",
                        "active",
                        "legacy",
                        "inventoryLevels",
                    }
                )
            },
        )
        response: "LocationConnection" = query.execute(client)
        return response

    @property
    def location_ids(self) -> list["ID"]:
        loc_ids = [loc.id for loc in self.locations.nodes if loc.id]
        return loc_ids

    @property
    def publications(self) -> "PublicationConnection":
        from shopify_sdk import client
        from shopify_sdk.gql.queries import publications

        query = publications(
            field_inclusions={
                "Publication": set({"id", "name", "status", "publishedAt", "updatedAt"})
            },
        )
        response = query.execute(client)
        return response


store = StoreManager()
