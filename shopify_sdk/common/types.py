from copy import deepcopy
from typing import Any, Optional

from pydantic import BaseModel, Field, PrivateAttr
from shopify_sdk.gql.core.types import Product, MetafieldInput


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
    metafields_init: Optional[list[MetafieldInput]] = Field(
        default=None,
        alias="metafields",
        validation_alias="metafields",
        exclude=True,
    )
    _metafields: list[MetafieldInput] = PrivateAttr(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        if self.metafields_init:
            self._set_metafields(self.metafields_init)
            self.metafields_init = None

    @property
    def metafields(self) -> list[MetafieldInput]:
        """Return a deep copy of metafields to prevent accidental mutation."""
        return deepcopy(self._metafields)

    def clear_metafields(self) -> None:
        self._metafields.clear()

    def add_metafield(
        self,
        *,
        namespace: str,
        key: str,
        type: str,
        value: str,
        id: Optional[str] = None,
    ) -> MetafieldInput:
        """Create a MetafieldInput and store it on the proxy product."""
        metafield = MetafieldInput(
            id=id,
            key=key,
            namespace=namespace,
            type=type,
            value=value,
        )
        self._metafields.append(metafield)
        return metafield

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
        hydrated = cls().hydrate(product)
        return hydrated or cls()
    
    def hydrate(self, product: Optional[Product] = None) -> Optional["ProxyProduct"]:
        from shopify_sdk.common.product import product_by_sku
        target_product: Optional[Product] = product
        if target_product is None:
            if self.sku is None:
                return None
            target_product = product_by_sku(self.sku)

        if target_product is None:
            return None

        try:
            self.id = target_product.id
            self.title = target_product.title
            self.description_html = target_product.descriptionHtml
            self.vendor = target_product.vendor
            self.type = target_product.productType
            self.tags = list(target_product.tags)
            self.seo_title = target_product.seo.title
            self.seo_description = target_product.seo.description
            
            # Hydrate metafields if present
            hydrated_metafields: list[MetafieldInput] = []
            if hasattr(target_product, 'metafields') and target_product.metafields:
                if hasattr(target_product.metafields, 'nodes') and target_product.metafields.nodes:
                    hydrated_metafields = [
                        MetafieldInput(
                            id=mf.id,
                            key=mf.key,
                            namespace=mf.namespace,
                            type=mf.type,
                            value=mf.value
                        )
                        for mf in target_product.metafields.nodes
                    ]
            self._set_metafields(hydrated_metafields)
            
            first_variant = None
            variants = target_product.variants
            if variants and variants.nodes:
                first_variant = variants.nodes[0]

            if not first_variant:
                raise ValueError("No variants found for the product.")
            
            self.sku = first_variant.sku
            self.price = first_variant.price
            self.quantity = first_variant.inventoryQuantity
        except Exception:
            return None

        return self

    def _set_metafields(self, metafields: list[MetafieldInput]) -> None:
        """Overwrite internal metafield cache with defensive copies."""
        self._metafields = [mf.model_copy(deep=True) for mf in metafields]
