from .core.client import ShopifyClientWrapper
from .variant import ProductVariantFactory, ProductVariant


class InformedClient(ShopifyClientWrapper):

    def __init__(self, shop_domain: str, access_token: str):
        super().__init__(shop_domain=shop_domain, access_token=access_token)
        self.ProductVariant = ProductVariantFactory(self)
    