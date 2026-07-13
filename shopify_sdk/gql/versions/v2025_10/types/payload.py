from typing import Dict

from shopify_sdk.gql.core.types.base import AutoRegisterModel
from .objects import *


class ProductCreatePayload(AutoRegisterModel):
    product: Optional[Product] = Field(default=None)
    shop: Optional[Shop] = Field(default=None)
    userErrors: List[UserError]


class StagedUploadsCreatePayload(AutoRegisterModel):
    stagedTargets: List[StagedMediaUploadTarget]
    userErrors: List[UserError]


class BulkOperationRunQueryPayload(AutoRegisterModel):
    bulkOperation: Optional[BulkOperation] = Field(default=None)
    userErrors: List[BulkOperationUserError]


class BulkOperationRunMutationPayload(AutoRegisterModel):
    bulkOperation: Optional[BulkOperation] = Field(default=None)
    userErrors: List[BulkOperationUserError]


class BulkOperationResultPayload(AutoRegisterModel):
    data: Optional[Dict] = Field(default={})
    lineNumber: Optional[int] = Field(alias="__lineNumber", default=None)
    errors: Optional[List[Dict]] = Field(default=None)


class ProductUpdatePayload(AutoRegisterModel):
    product: Optional[Product] = Field(default=None)
    userErrors: List[UserError]


class ProductUnpublishPayload(AutoRegisterModel):
    product: Optional[Product] = Field(default=None)
    shop: Optional[Shop] = Field(default=None)
    userErrors: List[UserError]


class ProductCreateMediaPayload(AutoRegisterModel):
    media: List[Media]
    mediaUserErrors: List[UserError]


class FileUpdatePayload(AutoRegisterModel):
    files: List[Media]
    userErrors: List[UserError]


class FileDeletePayload(AutoRegisterModel):
    deletedFileIds: List[ID]
    userErrors: List[UserError]


class ProductDeletePayload(AutoRegisterModel):
    deletedProductId: Optional[ID] = Field(default=None)
    userErrors: List[UserError]


class FulfillmentCreatePayload(AutoRegisterModel):
    fulfillment: Optional[Fulfillment] = Field(default=None)
    userErrors: List[UserError]


class FulfillmentCreateV2Payload(AutoRegisterModel):
    fulfillment: Optional[Fulfillment] = Field(default=None)
    userErrors: List[UserError]


class OrderCreatePayload(AutoRegisterModel):
    order: Optional[Order] = Field(default=None)
    userErrors: List[UserError]


class OrderUpdatePayload(AutoRegisterModel):
    order: Optional[Order] = Field(default=None)
    userErrors: List[UserError]


class DeliveryProfileUpdatePayload(AutoRegisterModel):
    profile: Optional[DeliveryProfile] = Field(default=None)
    userErrors: List[UserError]


class DeliveryProfileCreatePayload(AutoRegisterModel):
    profile: Optional[DeliveryProfile] = Field(default=None)
    userErrors: List[UserError]


class DeliveryProfileRemovePayload(AutoRegisterModel):
    job: Optional[Job] = Field(default=None)
    userErrors: List[UserError]


class OrderClosePayload(AutoRegisterModel):
    order: Optional[Order] = Field(default=None)
    userErrors: List[UserError]


class OrderOpenPayload(AutoRegisterModel):
    order: Optional[Order] = Field(default=None)
    userErrors: List[UserError]


class OrderMarkAsPaidPayload(AutoRegisterModel):
    order: Optional[Order] = Field(default=None)
    userErrors: List[UserError]


class OrderCancelPayload(AutoRegisterModel):
    job: Optional[Job] = Field(default=None)
    orderCancelUserErrors: List[OrderCancelUserError]


class ProductPublishPayload(AutoRegisterModel):
    product: Optional[Product] = Field(default=None)
    shop: Shop
    userErrors: List[UserError]


class InventoryAdjustQuantitiesPayload(AutoRegisterModel):
    userErrors: List[UserError]


class ProductVariantsBulkUpdateUserError(AutoRegisterModel):
    code: Optional[String] = Field(default=None)
    field: Optional[List[String]] = Field(default=None)
    message: String


class ProductVariantsBulkUpdatePayload(AutoRegisterModel):
    product: Optional[Product] = Field(default=None)
    productVariants: Optional[List[ProductVariant]] = Field(default=None)
    userErrors: List[ProductVariantsBulkUpdateUserError]


class ProductVariantsBulkCreateUserError(AutoRegisterModel):
    code: Optional[String] = Field(default=None)
    field: Optional[List[String]] = Field(default=None)
    message: String


class ProductVariantsBulkCreatePayload(AutoRegisterModel):
    product: Optional[Product] = Field(default=None)
    productVariants: Optional[List[ProductVariant]] = Field(default=None)
    userErrors: List[ProductVariantsBulkCreateUserError]
