from .types import Order, OrderIdentifierInput
from Shopify.core import Query

class orderByIdentifier(Query):
    return_type = Order

    def __init__(
        self,
        identifier: OrderIdentifierInput,
    ):
        self.identifier: OrderIdentifierInput = identifier