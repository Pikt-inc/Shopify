from .core import (
    Mutation,
    ProductUnpublishInput,
    OrderInput
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
