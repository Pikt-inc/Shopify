from .core import Query
from .core.types import Order, OrderConnection, OrderIdentifierInput, OrderSortKeys
from typing import Type, Optional
from pydantic import BaseModel

class orderByIdentifier(Query):
    return_type: Type[BaseModel] = Order

    def __init__(
        self,
        identifier: OrderIdentifierInput,
    ):
        self.identifier: OrderIdentifierInput = identifier


class orders(Query):
    return_type: Type[BaseModel] = OrderConnection
    _connection_arguments = {
        # Keep nested connections small so the latest orders payload stays lean.
        "fulfillmentOrders": {"first": 5},
        "lineItems": {"first": 5},
    }

    def __init__(
        self,
        first: int = 1,
        sortKey: OrderSortKeys = OrderSortKeys.PROCESSED_AT,
        reverse: bool = True,
        query: Optional[str] = None,
        after: Optional[str] = None,
    ):
        self.first: int = first
        self.sortKey: OrderSortKeys = sortKey
        self.reverse: bool = reverse
        self.query: Optional[str] = query
        self.after: Optional[str] = after
