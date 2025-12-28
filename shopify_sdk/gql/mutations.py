from pydantic import BaseModel, Field
from .core import Mutation
from .core.types.input_objects import *
from .core.types.payload import *
from typing import Type, Any, Dict, Set, Optional


class productUnpublish(Mutation):

    def __init__(
        self,
        input: ProductUnpublishInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.input: ProductUnpublishInput = input
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class productUpdate(Mutation):
    return_type: Type[BaseModel] = ProductUpdatePayload

    def __init__(
        self,
        product: ProductUpdateInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.product: ProductUpdateInput = product
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}
    

class productCreate(Mutation):
    return_type: Type[BaseModel] = ProductCreatePayload
    def __init__(
        self,
        product: ProductCreateInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.product: ProductCreateInput = product
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class productSet(Mutation):
    def __init__(
        self,
        input: ProductSetInput,
        synchronous: Boolean = False,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.input: ProductSetInput = input
        self.synchronous: Boolean = synchronous
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class productPublish(Mutation):
    def __init__(
        self,
        input: ProductPublishInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.input: ProductPublishInput = input
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class productVariantsBulkUpdate(Mutation):
    def __init__(
        self,
        productId: ID,
        variants: list[ProductVariantsBulkInput],
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.productId: ID = productId
        self.variants: list[ProductVariantsBulkInput] = variants
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class productVariantsBulkCreate(Mutation):
    def __init__(
        self,
        productId: ID,
        variants: list[ProductVariantsBulkInput],
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.productId: ID = productId
        self.variants: list[ProductVariantsBulkInput] = variants
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class orderUpdate(Mutation):
    def __init__(
        self,
        input: OrderInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.input: OrderInput = input
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class fulfillmentCreateV2(Mutation):
    def __init__(
        self,
        fulfillment: FulfillmentV2Input,
        message: String = "",
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.fulfillment: FulfillmentV2Input = fulfillment
        self.message: String = message
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class inventoryAdjustQuantities(Mutation):
    def __init__(
        self,
        input: InventoryAdjustQuantitiesInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.input: InventoryAdjustQuantitiesInput = input
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class productCreateMedia(Mutation):
    def __init__(
        self,
        media: list[CreateMediaInput],
        productId: ID,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.media: list[CreateMediaInput] = media
        self.productId: ID = productId
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class fileUpdate(Mutation):
    def __init__(
        self,
        files: list[FileUpdateInput],
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.files: list[FileUpdateInput] = files
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


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


class bulkOperationRunMutation(Mutation):
    return_type: Type[BaseModel] = BulkOperationRunMutationPayload

    def __init__(
        self,
        mutation: String,
        stagedUploadPath: String,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.mutation: String = mutation
        self.stagedUploadPath: String = stagedUploadPath
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class bulkOperationRunQuery(Mutation):
    return_type: Type[BaseModel] = BulkOperationRunQueryPayload

    def __init__(
        self,
        query: String,
        groupObjects: Boolean = True,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.query: String = query
        self.groupObjects: Boolean = groupObjects
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}