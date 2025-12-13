from __future__ import annotations
from typing import TYPE_CHECKING

from .base import connection

if TYPE_CHECKING:
    from .edges import (
        OrderEdge,
        LineItemEdge,
        FulfillmentOrderEdge
    )
    from .objects import (
        Order,
        LineItem,
        PageInfo,
        FulfillmentOrder
    )


class OrderConnection(connection):
    edges: list["OrderEdge"]
    nodes: list["Order"]
    pageInfo: "PageInfo"


class LineItemConnection(connection):
    edges: list["LineItemEdge"]
    nodes: list["LineItem"]
    pageInfo: "PageInfo"


class FulfillmentOrderConnection(connection):
    edges: list["FulfillmentOrderEdge"]
    nodes: list["FulfillmentOrder"]
    pageInfo: "PageInfo"
