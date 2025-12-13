from shopify_sdk import (
    client,
    orderUpdate,
    OrderIdentifierInput,
    orderByIdentifier,
    Order,
    
)
from shopify_sdk.gql.core.types import FulfillmentV2Input, FulfillmentTrackingInput, FulfillmentOrderLineItemsInput
from shopify_sdk.gql import fulfillmentCreateV2

from shopify_sdk.gql.core.types.input_objects import OrderInput







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

