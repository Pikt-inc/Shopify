from pydantic import BaseModel, Field
from typing import Optional
from shopify_sdk.gql.core.types import Product


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
        from shopify_sdk.common.actions import create_product

        product_id = create_product(product=self)
        self.id = product_id
        return product_id

    def update_or_create(self) -> Optional[str]:
        from shopify_sdk.common.actions import create_product, update_product
        from shopify_sdk.common.product import product_by_sku

        product_id = self.id

        if not product_id and self.sku:
            try:
                product = product_by_sku(self.sku)
                product_id = getattr(product, "id", None)
            except Exception:
                product_id = None

        if product_id:
            self.id = product_id
            product_id = update_product(product=self)
        else:
            product_id = create_product(product=self)

        self.id = product_id
        return product_id
    
    @classmethod
    def get(cls, sku: str) -> Optional["ProxyProduct"]:
        from shopify_sdk.common.product import product_by_sku
        product = product_by_sku(sku)
        if not product:
            return cls()
        return cls().hydrate(product)
    
    def hydrate(self, product: Product) -> Optional["ProxyProduct"]:
        if not product:
            return None

        try:
            self.id = product.id
            self.title = product.title
            self.description_html = product.descriptionHtml
            self.vendor = product.vendor
            self.type = product.productType
            self.tags = list(product.tags)
            self.seo_title = product.seo.title
            self.seo_description = product.seo.description
            first_variant = None
            variants = product.variants
            if variants and variants.nodes:
                first_variant = variants.nodes[0]

            if not first_variant:
                raise ValueError("No variants found for the product.")
            
            self.sku = first_variant.sku
            price = first_variant.price
            self.price = price.amount if price is not None else None
            self.quantity = first_variant.inventoryQuantity
        except Exception:
            return self

        return self
