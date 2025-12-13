from typing import Optional

from .gql import ID
from shopify_sdk import (
        OrderIdentifierInput,
        orderByIdentifier,
        Order,
        client
    )
from shopify_sdk.gql.core.types import FulfillmentV2Input, FulfillmentTrackingInput, FulfillmentOrderLineItemsInput
from shopify_sdk.gql import fulfillmentCreateV2

from shopify_sdk.gql.core.types.input_objects import OrderInput
import logging

logger = logging.getLogger(__name__)


def retrieve_order(
    order_id: ID
) -> Optional[Order]:
    """
    Retrieves an order by its unique identifier.

    Args:
        order_id (ID): The unique identifier of the order.

    Returns:
        Optional[Order]: The Order object if found, otherwise None.
    """
    identifier = OrderIdentifierInput(id=order_id)
    queried_order: Optional[Order] = orderByIdentifier(
        identifier=identifier
    ).execute(client=client)
    return queried_order

def retrieve_order_line_items(
    order_id: ID
) -> Optional[Order]:
    """
    Retrieves an order along with its fulfillment information by its unique identifier.

    Args:
        order_id (ID): The unique identifier of the order.

    Returns:
        Optional[Order]: The Order object with fulfillment details if found, otherwise None.
    """
    order = retrieve_order(order_id)
    if order.lineItems.count == 0:
        return None
    return order.lineItems.nodes

def set_order_tracking(
    order_id: ID,
    line_item_id: ID,
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
    line_items = retrieve_order_line_items(order_id)
    if line_items is None:
        logger.error(f"No line items found for order {order_id}.")
        return False
    
    valid_line_items = [li.id for li in line_items]
    if line_item_id not in valid_line_items:
        logger.error(f"Line item ID {line_item_id} not found in order {order_id}.")
        return False
    
    f = FulfillmentOrderLineItemsInput(
        fulfillmentOrderId=line_item_id,

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
        logger.error(f"Error setting tracking info: {e}")
        return False


    
