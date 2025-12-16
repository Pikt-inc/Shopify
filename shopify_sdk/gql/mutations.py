from .core import Mutation
from .core.types.input_objects import *

class productUnpublish(Mutation):

    def __init__(
        self,
        input: ProductUnpublishInput,
    ):
        self.input: ProductUnpublishInput = input


class productUpdate(Mutation):
    def __init__(
        self,
        product: ProductUpdateInput
    ):
        self.product: ProductUpdateInput = product
    
    @property
    def fields(self) -> str:
        spacer = " " * (self._indent * 2)
        inner = " " * (self._indent * 3)
        product_block = "\n".join(
            [
                f"{spacer}product {{",
                f"{inner}id",
                f"{spacer}}}",
            ]
        )
        return "\n".join([product_block, self._user_errors_block])

    
class productCreate(Mutation):
    def __init__(
        self,
        product: ProductCreateInput,
    ):
        self.product: ProductCreateInput = product

    @property
    def fields(self) -> str:
        spacer = " " * (self._indent * 2)
        inner = " " * (self._indent * 3)
        product_block = "\n".join(
            [
                f"{spacer}product {{",
                f"{inner}id",
                f"{spacer}}}",
            ]
        )
        return "\n".join([product_block, self._user_errors_block])


class productPublish(Mutation):
    def __init__(
        self,
        input: ProductPublishInput,
    ):
        self.input: ProductPublishInput = input

    @property
    def fields(self) -> str:
        spacer = " " * (self._indent * 2)
        inner = " " * (self._indent * 3)
        product_block = "\n".join(
            [
                f"{spacer}product {{",
                f"{inner}id",
                f"{spacer}}}",
            ]
        )
        return "\n".join([product_block, self._user_errors_block])


class productVariantsBulkUpdate(Mutation):
    def __init__(
        self,
        productId: ID,
        variants: list[ProductVariantsBulkInput],
    ):
        self.productId: ID = productId
        self.variants: list[ProductVariantsBulkInput] = variants


class productVariantsBulkCreate(Mutation):
    def __init__(
        self,
        productId: ID,
        variants: list[ProductVariantsBulkInput],
    ):
        self.productId: ID = productId
        self.variants: list[ProductVariantsBulkInput] = variants


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


class inventoryAdjustQuantities(Mutation):
    def __init__(
        self,
        input: InventoryAdjustQuantitiesInput,
    ):
        self.input: InventoryAdjustQuantitiesInput = input


class productCreateMedia(Mutation):
    def __init__(
        self,
        media: list[CreateMediaInput],
        productId: ID,
    ):
        self.media: list[CreateMediaInput] = media
        self.productId: ID = productId
    
    @property
    def fields(self) -> str:
        spacer = " " * (self._indent * 2)
        inner = " " * (self._indent * 3)
        media_block = "\n".join(
            [
                f"{spacer}media {{",
                f"{inner}id",
                f"{spacer}}}",
            ]
        )
        return "\n".join([media_block, self._user_errors_block])
