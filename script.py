from shopify_sdk.gql import orders
from shopify_sdk.gql.core.types import OrderSortKeys
from shopify_sdk import client
from typing import Iterable
from shopify_sdk.gql.core.types import Order

def iter_orders() -> Iterable[Order]:
    latest = orders(
        first=25,
        sortKey=OrderSortKeys.PROCESSED_AT,
        reverse=True,
        field_exclusions={
            "Order": set(
                Order.fields_except(
                    exclude=["id", "shippingAddress", "displayAddress"]
                )
            )
        }
    ).execute(client=client)
    for order in latest.nodes:
        yield order
    
for order in iter_orders():
    print(order.id, order.displayAddress)
