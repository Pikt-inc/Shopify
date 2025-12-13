from .types import Order, OrderIdentifierInput
from Shopify.core import Query
from typing import Type, Optional
from pydantic import BaseModel

class orderByIdentifier(Query):
    return_type: Type[BaseModel] = Order  # Reference the class directly

    def __init__(
        self,
        identifier: OrderIdentifierInput,
    ):
        self.identifier: OrderIdentifierInput = identifier