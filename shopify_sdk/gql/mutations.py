from pydantic import BaseModel
from .core import Mutation
from .core.types.input_objects import *
from .core.types.payload import *
from .core.types.enums import OrderCancelReason
from typing import Type, Dict, Set, Optional


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
        media: Optional[list[CreateMediaInput]] = None,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.media: Optional[list[CreateMediaInput]] = media
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


class productDelete(Mutation):
    return_type: Type[BaseModel] = ProductDeletePayload

    def __init__(
        self,
        input: ProductDeleteInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.input: ProductDeleteInput = input
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class deliveryProfileUpdate(Mutation):
    return_type: Type[BaseModel] = DeliveryProfileUpdatePayload

    def __init__(
        self,
        id: ID,
        profile: DeliveryProfileInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.id: ID = id
        self.profile: DeliveryProfileInput = profile
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class deliveryProfileCreate(Mutation):
    return_type: Type[BaseModel] = DeliveryProfileCreatePayload

    def __init__(
        self,
        profile: DeliveryProfileInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.profile: DeliveryProfileInput = profile
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class deliveryProfileRemove(Mutation):
    return_type: Type[BaseModel] = DeliveryProfileRemovePayload

    def __init__(
        self,
        id: ID,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.id: ID = id
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class productSet(Mutation):
    return_type: Type[BaseModel] = ProductSetPayload

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
    return_type: Type[BaseModel] = ProductPublishPayload

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
    return_type: Type[BaseModel] = ProductVariantsBulkUpdatePayload

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


class orderCreate(Mutation):
    return_type: Type[BaseModel] = OrderCreatePayload

    def __init__(
        self,
        order: OrderCreateOrderInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.order: OrderCreateOrderInput = order
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class orderClose(Mutation):
    return_type: Type[BaseModel] = OrderClosePayload

    def __init__(
        self,
        input: OrderCloseInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.input: OrderCloseInput = input
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class orderOpen(Mutation):
    return_type: Type[BaseModel] = OrderOpenPayload

    def __init__(
        self,
        input: OrderOpenInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.input: OrderOpenInput = input
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class orderMarkAsPaid(Mutation):
    return_type: Type[BaseModel] = OrderMarkAsPaidPayload

    def __init__(
        self,
        input: OrderMarkAsPaidInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.input: OrderMarkAsPaidInput = input
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class orderCancel(Mutation):
    return_type: Type[BaseModel] = OrderCancelPayload

    def __init__(
        self,
        orderId: ID,
        restock: Boolean,
        reason: OrderCancelReason,
        notifyCustomer: Optional[Boolean] = None,
        staffNote: Optional[String] = None,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.orderId: ID = orderId
        self.restock: Boolean = restock
        self.reason: OrderCancelReason = reason
        self.notifyCustomer: Optional[Boolean] = notifyCustomer
        self.staffNote: Optional[String] = staffNote
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class fulfillmentCreate(Mutation):
    return_type: Type[BaseModel] = FulfillmentCreatePayload

    def __init__(
        self,
        fulfillment: FulfillmentInput,
        message: String = "",
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.fulfillment: FulfillmentInput = fulfillment
        self.message: String = message
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
    return_type: Type[BaseModel] = ProductCreateMediaPayload

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
    return_type: Type[BaseModel] = FileUpdatePayload

    def __init__(
        self,
        files: list[FileUpdateInput],
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.files: list[FileUpdateInput] = files
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class fileDelete(Mutation):
    return_type: Type[BaseModel] = FileDeletePayload

    def __init__(
        self,
        fileIds: list[ID],
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.fileIds: list[ID] = fileIds
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
