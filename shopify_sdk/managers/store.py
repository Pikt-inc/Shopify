from typing import TYPE_CHECKING
from pydantic import BaseModel, Field

from .products import ProductManager
from .orders import OrderManager
from .delivery import DeliveryManager

if TYPE_CHECKING:
    from shopify_sdk.gql.core.types.connections import (
        LocationConnection, PublicationConnection
    )

class StoreManager(BaseModel):
    products: ProductManager = Field(default_factory=ProductManager)
    orders: OrderManager = Field(default_factory=OrderManager)
    delivery: DeliveryManager = Field(default_factory=DeliveryManager)
    model_config = {
        "arbitrary_types_allowed": True,
    }

    @property
    def locations(self) -> "LocationConnection":
        from shopify_sdk import client
        from shopify_sdk.gql.queries import locations
        query = locations(
            field_inclusions={
                "Location": set(
                    {
                        "id", "name", "address", "city",
                        "country", "province", "zip", "active",
                        "legacy", "inventoryLevels"
                    }
                )
            },
        )
        response: "LocationConnection" = query.execute(client)
        return response
    
    @property
    def publications(self) -> "PublicationConnection":
        from shopify_sdk import client
        from shopify_sdk.gql.queries import publications
        query = publications(
            field_inclusions={
                "Publication": set(
                    {
                        "id", "name", "status",
                        "publishedAt", "updatedAt"
                    }
                )
            },
        )
        response: "PublicationConnection" = query.execute(client)
        return response


store = StoreManager()
