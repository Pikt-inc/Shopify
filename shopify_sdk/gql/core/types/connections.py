from __future__ import annotations
from typing import TYPE_CHECKING

from .base import connection

if TYPE_CHECKING:
    from .edges import (
        OrderLineItemEdge,
        FulfillmentOrderEdge
    )
    from .objects import (
        OrderLineItem,
        PageInfo,
        FulfillmentOrder
    )


class OrderLineItemConnection(connection):
    edges: list["OrderLineItemEdge"]
    nodes: list["OrderLineItem"]
    pageInfo: "PageInfo"


class FulfillmentOrderConnection(connection):
    edges: list["FulfillmentOrderEdge"]
    nodes: list["FulfillmentOrder"]
    pageInfo: "PageInfo"

