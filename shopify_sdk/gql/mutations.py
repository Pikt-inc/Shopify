from .core import (
    Mutation
)
from .core.types import (
    ProductUnpublishInput,
    OrderInput,
    String,
    FulfillmentV2Input
)

class productUnpublish(Mutation):

    def __init__(
        self,
        input: ProductUnpublishInput,
    ):
        self.input: ProductUnpublishInput = input


class orderUpdate(Mutation):
    def __init__(
        self,
        input: OrderInput
    ):
        self.input: OrderInput = input


class fulfillmentCreateV2(Mutation):
    def __init__(
        self,
        fulfillment: FulfillmentV2Input,
        message: String = "",
    ):
        self.fulfillment: FulfillmentV2Input = fulfillment
        self.message: String = message
