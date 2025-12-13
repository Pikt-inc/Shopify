from __future__ import annotations
from typing import TYPE_CHECKING

from .base import edge

if TYPE_CHECKING:
    from .objects import Order, LineItem, FulfillmentOrder


class OrderEdge(edge):
    node: "Order"

class LineItemEdge(edge):
    node: "LineItem"

class FulfillmentOrderEdge(edge):
    node: "FulfillmentOrder"
