from shopify_sdk.gql.core.types import (
    OrderIdentifierInput,
    Order
)
from shopify_sdk.gql import (
    orderByIdentifier
)
from shopify_sdk import client

# identifier = OrderIdentifierInput(id="gid://shopify/Order/6753283801339")
# res: Order = orderByIdentifier(
#     identifier=identifier,
#     field_inclusions={
#         "Order": {"lineItems"}
#     }

# ).execute(client=client)

identifier = OrderIdentifierInput(id="gid://shopify/Order/6753283801339")
res: Order = orderByIdentifier(
    identifier=identifier,
    field_inclusions={
        "Order": {"lineItems"}
    },
    field_exclusions={
        "LineItem": {"variant"}
    },
    connection_arguments = {
        "lineItems": {"first": 100},
    }

).execute(client=client)

print(type(res))
print(len(res.lineItems.edges))
