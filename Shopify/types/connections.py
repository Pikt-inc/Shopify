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
    def count(self) -> int:
        return len(self.edges)
    
    @property
    def first(self) -> "OrderLineItem | None":
        return self.nodes[0] if self.nodes else None
    
    @property
    def second(self) -> "OrderLineItem | None":
        return self.nodes[1] if len(self.nodes) > 1 else None
    
    @property
    def third(self) -> "OrderLineItem | None":
        return self.nodes[2] if len(self.nodes) > 2 else None
    
    @property
    def last(self) -> "OrderLineItem | None":
        return self.nodes[-1] if self.nodes else None
    

