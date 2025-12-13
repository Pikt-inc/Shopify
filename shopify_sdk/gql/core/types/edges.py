from __future__ import annotations
from typing import TYPE_CHECKING

from .base import edge

if TYPE_CHECKING:
    from .objects import Order, OrderLineItem, FulfillmentOrder


class OrderEdge(edge):
    node: "Order"

class OrderLineItemEdge(edge):
    node: "OrderLineItem"

class FulfillmentOrderEdge(edge):
    node: "FulfillmentOrder"
