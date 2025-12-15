from pydantic import BaseModel

class ProductActionResponse(BaseModel):
    action: str
    success: bool
    message: str | None = None
    sku: str | None = None
