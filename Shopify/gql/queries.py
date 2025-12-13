from .core import Query, Order, OrderIdentifierInput
from typing import Type, Optional
from pydantic import BaseModel

class orderByIdentifier(Query):
    return_type: Type[BaseModel] = Order

    def __init__(
        self,
        identifier: OrderIdentifierInput,
    ):
        self.identifier: OrderIdentifierInput = identifier
