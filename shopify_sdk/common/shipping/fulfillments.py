from typing import Optional

from shopify_sdk.gql.core.types import (
    OrderIdentifierInput,
    Order,
    LineItem,
    FulfillmentOrderLineItem,
    FulfillmentTrackingInput,
    FulfillmentV2Input,
    ID,
    Boolean,
    String,
    FulfillmentOrderLineItemsInput,
    FulfillmentOrderLineItemInput,
)
from shopify_sdk.gql.core.types.objects import FulfillmentOrder
from shopify_sdk.gql import fulfillmentCreateV2
from shopify_sdk.gql import (
    orderByIdentifier
)
from shopify_sdk import client


def get_fulfillments_by_order_id(
    order_id: ID
    ) -> list[FulfillmentOrder]:
    identifier = OrderIdentifierInput(id=order_id)
    res: Order = orderByIdentifier(
        identifier=identifier,
        field_inclusions={
            "Order": {"fulfillmentOrders"}
        },
        field_exclusions={
            "FulfillmentOrder": {"channelId", "createdAt", "fulfillAt", "fulfillBy"},
            "FulfillmentOrderLineItem": set(
                FulfillmentOrderLineItem.fields_except(exclude=["id", "lineItem"])
            ),
            "LineItem": set(LineItem.fields_except(exclude=["id"])),
        },
        connection_arguments={
            "fulfillmentOrders": {"first": 100},
        }

    ).execute(client=client)
    return res.fulfillmentOrders.nodes


def set_order_line_item_tracking(
    order_id: ID,
    line_item_id: ID,
    tracking_number: String,
    carrier: String,
    quantity: int = 1
) -> None:
    fulfillments = get_fulfillments_by_order_id(order_id)
    valid_fli: Optional[FulfillmentOrderLineItem] = None
    fulfillment_id: Optional[ID] = None
    for fulfillment in fulfillments:
        for fline_item in fulfillment.lineItems.nodes:
            if fline_item.lineItem.id == line_item_id:
                valid_fli = fline_item
                fulfillment_id = fulfillment.id
                break
        if valid_fli:
            break

    if not valid_fli:
        raise ValueError(f"Line item {line_item_id} not found in order {order_id} fulfillment orders.")

    tracking = FulfillmentTrackingInput(
        company=carrier,
        number=tracking_number
    )
    f: FulfillmentOrderLineItemsInput = FulfillmentOrderLineItemsInput(
        fulfillmentOrderId=fulfillment_id,
        fulfillmentOrderLineItems=[
            FulfillmentOrderLineItemInput(
                id=valid_fli.id,
                quantity=quantity
            )
        ]
    )
    fulfillment_input = FulfillmentV2Input(
        lineItemsByFulfillmentOrder=[f],
        trackingInfo=tracking
    )

    fulfillmentCreateV2(
        fulfillment=fulfillment_input
    ).execute(client=client)
    
