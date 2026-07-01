"""Create or update products with Shopify's productSet mutation."""

from __future__ import annotations

import os

from shopify_sdk import store
from shopify_sdk.gql.core.types import ProductSetInput


def build_product() -> ProductSetInput:
    """Build one typed productSet input payload."""

    return ProductSetInput(
        handle="example-product",
        title="Example Product",
        descriptionHtml="<p>Created through shopify_sdk.</p>",
        productType="Demo",
        vendor="Example Vendor",
        tags=["example", "sdk"],
    )


def main() -> None:
    """Submit the productSet payload to the configured Shopify store."""

    with store.credentials_context(
        shop_domain=os.environ["SHOPIFY_SHOP_DOMAIN"],
        access_token=os.environ["SHOPIFY_ACCESS_TOKEN"],
        api_version=os.getenv("SHOPIFY_API_VERSION", "2025-10"),
    ):
        payloads = store.products.bulk.set([build_product()])

    for payload in payloads:
        operation = getattr(payload, "productSetOperation", None)
        print(getattr(operation, "id", None), getattr(operation, "status", None))


if __name__ == "__main__":
    main()
