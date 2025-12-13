from __future__ import annotations
from typing import TYPE_CHECKING

from .base import edge

if TYPE_CHECKING:
    from .objects import OrderLineItem, FulfillmentOrder

class OrderLineItemEdge(edge):
    node: "OrderLineItem"

class FulfillmentOrderEdge(edge):
    node: "FulfillmentOrder"