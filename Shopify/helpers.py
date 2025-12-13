from .gql import ID
from Shopify import (
        OrderIdentifierInput,
        orderByIdentifier,
        Order,
        client
    )
from Shopify.gql.core.types import FulfillmentV2Input, FulfillmentTrackingInput, FulfillmentOrderLineItemsInput
from Shopify.gql import fulfillmentCreateV2

from Shopify.gql.core.types.input_objects import OrderInput


def set_order_tracking(
    order_id: ID,
    tracking_number: str,
    carrier: str        
):
    """
    Sets the tracking information for a given order.

    Args:
        order_id (ID): The unique identifier of the order.
        tracking_number (str): The tracking number provided by the carrier.
        carrier (str): The name of the shipping carrier. 
    Returns:
        bool: True if the tracking information was set successfully, False otherwise.
    """
    identifier = OrderIdentifierInput(id=order_id)
    queried_order: Order = orderByIdentifier(
        identifier=identifier
    ).execute(client=client)
    if not queried_order or not \
        queried_order.fulfillmentOrders or \
            len(queried_order.fulfillmentOrders) == 0:
        return False
    fulfillment_order = queried_order.fulfillmentOrders.first
    f = FulfillmentOrderLineItemsInput(
        fulfillmentOrderId=fulfillment_order.id,

    )
    tracking = FulfillmentTrackingInput(
        company=carrier,
        number=tracking_number
    )
    fulfillment_input = FulfillmentV2Input(
        lineItemsByFulfillmentOrder=[f],
        trackingInfo=tracking
    )
    try:
        fulfillmentCreateV2(
            fulfillment=fulfillment_input
        ).execute(client=client)
        return True
    except Exception as e:
        print(f"Error setting tracking info: {e}")
        return False


    

