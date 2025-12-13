from __future__ import annotations
from typing import TYPE_CHECKING

from .base import connection

if TYPE_CHECKING:
    from .edges import OrderLineItemEdge
    from .objects import OrderLineItem, PageInfo


class OrderLineItemConnection(connection):
    edges: list["OrderLineItemEdge"]
    nodes: list["OrderLineItem"]
    pageInfo: "PageInfo"

    @property
    def first(self) -> "OrderLineItem | None":
        return self.nodes[0] if self.nodes else None
