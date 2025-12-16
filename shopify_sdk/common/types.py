from pydantic import BaseModel, Field
from typing import Optional


class ProxyProduct(BaseModel):
    id: Optional[str] = Field(default=None)
    sku: Optional[str] = Field(default=None)
    title: Optional[str] = Field(default=None)
    description_html: Optional[str] = Field(default=None)
    vendor: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None)
    tags: Optional[list[str]] = Field(default=None)
    price: Optional[str] = Field(default=None)
    seo_title: Optional[str] = Field(default=None)
    seo_description: Optional[str] = Field(default=None)
    quantity: Optional[int] = Field(default=0)

    def save(self) -> Optional[str]:
        if self.id:
            return self.id
        from shopify_sdk.common.actions import update_product

        product_id = update_product(product=self)
        self.id = product_id
        return product_id
