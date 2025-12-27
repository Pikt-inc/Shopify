from typing import Type, Optional, Dict, Set
from pydantic import BaseModel

from .core import Mutation
from .core.types.input_objects import *
from .core.types.payloads import *

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


class productSet(Mutation):
    return_type: Type[BaseModel] = ProductSetPayload

    def __init__(
        self,
        input: ProductSetInput,
        identifier: Optional[ProductSetIdentifiers] = None,
        synchronous: Optional[Boolean] = False,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.identifier: Optional[ProductSetIdentifiers] = identifier
        self.input: ProductSetInput = input
        self.synchronous: Boolean = synchronous
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}
        

    # @property
    # def fields(self) -> str:
    #     spacer = " " * (self._indent * 2)
    #     inner = " " * (self._indent * 3)
    #     blocks = [
    #         "\n".join(
    #             [
    #                 f"{spacer}product {{",
    #                 f"{inner}id",
    #                 f"{spacer}}}",
    #             ]
    #         ),
    #         "\n".join(
    #             [
    #                 f"{spacer}productSetOperation {{",
    #                 f"{inner}id",
    #                 f"{inner}status",
    #                 f"{spacer}}}",
    #             ]
    #         ),
    #         self._user_errors_block,
    #     ]
    #     return "\n".join(blocks)


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


class fileUpdate(Mutation):
    def __init__(
        self,
        files: list[FileUpdateInput],
    ):
        self.files: list[FileUpdateInput] = files

    @property
    def fields(self) -> str:
        spacer = " " * (self._indent * 2)
        inner = " " * (self._indent * 3)
        files_block = "\n".join(
            [
                f"{spacer}files {{",
                f"{inner}id",
                f"{spacer}}}",
            ]
        )
        return "\n".join([files_block, self._user_errors_block])


class stagedUploadsCreate(Mutation):
    return_type: Type[BaseModel] = StagedUploadsCreatePayload
    def __init__(
        self,
        input: list[StagedUploadInput],
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.input: list[StagedUploadInput] = input
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}

    # @property
    # def fields(self) -> str:
    #     spacer = " " * (self._indent * 2)
    #     inner = " " * (self._indent * 3)
    #     deep = " " * (self._indent * 4)
    #     targets_block = "\n".join(
    #         [
    #             f"{spacer}stagedTargets {{",
    #             f"{inner}url",
    #             f"{inner}resourceUrl",
    #             f"{inner}parameters {{",
    #             f"{deep}name",
    #             f"{deep}value",
    #             f"{inner}}}",
    #             f"{spacer}}}",
    #         ]
    #     )
    #     return "\n".join([targets_block, self._user_errors_block])


class bulkOperationRunMutation(Mutation):
    def __init__(
        self,
        mutation: String,
        stagedUploadPath: String,
    ):
        self.mutation: String = mutation
        self.stagedUploadPath: String = stagedUploadPath

    @property
    def fields(self) -> str:
        spacer = " " * (self._indent * 2)
        inner = " " * (self._indent * 3)
        op_block = "\n".join(
            [
                f"{spacer}bulkOperation {{",
                f"{inner}id",
                f"{inner}status",
                f"{spacer}}}",
            ]
        )
        return "\n".join([op_block, self._user_errors_block])


class bulkOperationRunQuery(Mutation):
    def __init__(
        self,
        query: String,
    ):
        self.query: String = query

    @property
    def fields(self) -> str:
        spacer = " " * (self._indent * 2)
        inner = " " * (self._indent * 3)
        op_block = "\n".join(
            [
                f"{spacer}bulkOperation {{",
                f"{inner}id",
                f"{inner}status",
                f"{spacer}}}",
            ]
        )
        return "\n".join([op_block, self._user_errors_block])
