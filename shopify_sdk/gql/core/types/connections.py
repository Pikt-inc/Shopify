from __future__ import annotations
from typing import TYPE_CHECKING

from .base import connection

if TYPE_CHECKING:
    from .edges import (
        OrderEdge,
        OrderLineItemEdge,
        FulfillmentOrderEdge
    )
    from .objects import (
        Order,
        OrderLineItem,
        PageInfo,
        FulfillmentOrder
    )


class OrderConnection(connection):
    edges: list["OrderEdge"]
    nodes: list["Order"]
    pageInfo: "PageInfo"


class OrderLineItemConnection(connection):
    edges: list["OrderLineItemEdge"]
    nodes: list["OrderLineItem"]
    pageInfo: "PageInfo"


class FulfillmentOrderConnection(connection):
    edges: list["FulfillmentOrderEdge"]
    nodes: list["FulfillmentOrder"]
    pageInfo: "PageInfo"
