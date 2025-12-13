from Shopify import (
    client,
    orderUpdate,
    OrderIdentifierInput,
    orderByIdentifier,
    Order,
    
)
from Shopify.gql.core.types import FulfillmentV2Input, FulfillmentTrackingInput, FulfillmentOrderLineItemsInput
from Shopify.gql import fulfillmentCreateV2

from Shopify.gql.core.types.input_objects import OrderInput







f = FulfillmentOrderLineItemsInput(
    fulfillmentOrderId="gid://shopify/FulfillmentOrder/7823840084219",

)
tracking = FulfillmentTrackingInput(
    company="UPS",
    number="1Z999AA10123456784"
)
fulfillment_input = FulfillmentV2Input(
    lineItemsByFulfillmentOrder=[f],
    trackingInfo=tracking
)
mutation = fulfillmentCreateV2(
    fulfillment=fulfillment_input
).execute(client=client)

