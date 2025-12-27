from .base import AutoRegisterModel
from .objects import *


class ProductSetPayload(AutoRegisterModel):
    product: Product
    productSetOperation: ProductSetOperation
    userErrors: list[ProductSetUserError]


class StagedUploadsCreatePayload(AutoRegisterModel):
    stagedTargets: list[StagedMediaUploadTarget]
    userErrors: list[UserError]