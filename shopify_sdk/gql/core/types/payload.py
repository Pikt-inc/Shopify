from typing import Dict

from .base import AutoRegisterModel
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


class ProductUpdatePayload(AutoRegisterModel):
    product: Optional[Product] = Field(default=None)
    userErrors: List[UserError]
