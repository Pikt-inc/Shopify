from pydantic import BaseModel, Field

from .product import ProductManager


class StoreManager(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    products: ProductManager = Field(default_factory=ProductManager)


store = StoreManager()