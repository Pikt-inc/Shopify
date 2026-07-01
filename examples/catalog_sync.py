"""Build productSet payloads from an external catalog feed."""

from __future__ import annotations

import os
from dataclasses import dataclass

from shopify_sdk import store
from shopify_sdk.gql.core.types import ProductSetInput, ProductVariantSetInput


@dataclass(frozen=True)
class SourceCatalogItem:
    """Represent one external catalog item ready for Shopify mapping."""

    handle: str
    title: str
    sku: str
    price: str
    product_type: str
    vendor: str
    tags: tuple[str, ...]

    def to_product_set_input(self) -> ProductSetInput:
        """Convert the source item into a typed Shopify productSet payload."""

        return ProductSetInput(
            handle=self.handle,
            title=self.title,
            productType=self.product_type,
            vendor=self.vendor,
            tags=list(self.tags),
            variants=[self.to_variant_set_input()],
        )

    def to_variant_set_input(self) -> ProductVariantSetInput:
        """Convert the source item into a default Shopify variant payload."""

        return ProductVariantSetInput(sku=self.sku, price=self.price)


def build_catalog_payloads() -> list[ProductSetInput]:
    """Build example payloads that mirror an upstream catalog sync."""

    return [
        SourceCatalogItem(
            handle="example-catalog-product",
            title="Example Catalog Product",
            sku="EXAMPLE-SKU-001",
            price="24.99",
            product_type="Demo",
            vendor="Example Vendor",
            tags=("catalog-sync", "example"),
        ).to_product_set_input()
    ]


def main() -> None:
    """Submit mapped catalog payloads to the configured Shopify store."""

    with store.credentials_context(
        shop_domain=os.environ["SHOPIFY_SHOP_DOMAIN"],
        access_token=os.environ["SHOPIFY_ACCESS_TOKEN"],
        api_version=os.getenv("SHOPIFY_API_VERSION", "2025-10"),
    ):
        payloads = store.products.bulk.set(build_catalog_payloads())

    for payload in payloads:
        operation = getattr(payload, "productSetOperation", None)
        print(getattr(operation, "id", None), getattr(operation, "status", None))


if __name__ == "__main__":
    main()
