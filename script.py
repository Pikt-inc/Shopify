from shopify_sdk import (
    OrderIdentifierInput,
    orderByIdentifier,
    Order,
    client
)


identifier = OrderIdentifierInput(id="gid://shopify/Order/6753283801339")
res: Order = orderByIdentifier(
    identifier=identifier
).execute(client=client)

print()
print(type(res))
print(res.id)
print(res.returnStatus)
print(res.fulfillmentOrders.nodes)


