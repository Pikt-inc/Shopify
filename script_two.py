from Shopify import (
    client,
    orderUpdate,
    OrderIdentifierInput,
    orderByIdentifier,
    Order
)
from Shopify.gql.core.types.input_objects import OrderInput

oi = OrderInput(
    id="gid://shopify/Order/6753695596795",
    email="pkww31@gmail.com"
)

res = orderUpdate(
    input=oi
).execute(client=client)

print("User errors:", res, type(res))

identifier = OrderIdentifierInput(id="gid://shopify/Order/6753695596795")
res: Order = orderByIdentifier(
    identifier=identifier
).execute(client=client)

print()
print(type(res))
print(res.id)
print(res.returnStatus)
print(res.fulfillmentOrders.first)
