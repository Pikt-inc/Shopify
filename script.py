from Shopify.core.client import client
from Shopify import (
    OrderIdentifierInput,
    orderByIdentifier,
    Order
)


identifier = OrderIdentifierInput(id="gid://shopify/Order/6753695596795")
res: Order = orderByIdentifier(
    identifier=identifier
).execute(client=client)

print()
print(type(res))
print(res.id)
print(res.returnStatus)
print(res.fulfillmentOrders.first)


