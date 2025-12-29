from typing import List, Optional, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from shopify_sdk.gql.core.types.objects import Order
    from shopify_sdk.gql.core.types.base import ID


class OrderManager:
    @property
    def all(self) -> List["Order"]:
        from shopify_sdk.gql.queries import orders
        from shopify_sdk.gql.core.types.connections import OrderConnection

        query = orders(
            field_inclusions={
                "Order": set(
                    {
                        "id",
                        "name",
                        "email",
                        "createdAt",
                        "totalPriceSet",
                        "financialStatus",
                        "fulfillmentStatus",
                        "shippingAddress",
                        "billingAddress",
                        "tags",
                    }
                )
            },
        )
        response = cast(OrderConnection, query.bulk())
        return response.nodes

    def details(self, id: "ID") -> Optional["Order"]:
        from shopify_sdk.gql.queries import orderByIdentifier
        from shopify_sdk.gql.core.types.input_objects import OrderIdentifierInput
        from shopify_sdk import client

        identifier = OrderIdentifierInput(id=id)
        query = orderByIdentifier(
            identifier=identifier,
            field_inclusions={
                "Order": set(
                    {
                        "id",
                        "name",
                        "email",
                        "createdAt",
                        "totalPriceSet",
                        "financialStatus",
                        "fulfillmentStatus",
                        "shippingAddress",
                        "billingAddress",
                        "tags",
                        "lineItems",
                        "customer",
                        "discountApplications",
                    }
                ),
                "LineItemConnection": set({"nodes"}),
                "LineItem": set(
                    {
                        "id",
                        "sku",
                        "title",
                        "quantity",
                        "priceSet",
                        "totalDiscountSet",
                        "taxLines",
                        "product",
                    }
                ),
                "Product": set({"id"}),
            },
        )
        result: Optional["Order"] = query.execute(client)
        return result
