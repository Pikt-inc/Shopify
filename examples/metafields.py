"""Create or update a product payload with Shopify metafields."""

from __future__ import annotations

import os

from shopify_sdk import store
from shopify_sdk.gql.core.types import MetafieldInput, ProductSetInput


def build_product_with_metafields() -> ProductSetInput:
    """Build a typed productSet payload with product-level metafields."""

    return ProductSetInput(
        handle="example-metafield-product",
        title="Example Metafield Product",
        descriptionHtml="<p>Created through shopify_sdk with metafields.</p>",
        productType="Demo",
        vendor="Example Vendor",
        tags=["example", "sdk", "metafields"],
        metafields=[
            MetafieldInput(
                namespace="custom",
                key="material",
                type="single_line_text_field",
                value="Recycled aluminum",
            ),
            MetafieldInput(
                namespace="custom",
                key="care_instructions",
                type="multi_line_text_field",
                value="Wipe clean with a soft cloth.",
            ),
        ],
    )


def main() -> None:
    """Submit a metafield-backed productSet payload to Shopify."""

    with store.credentials_context(
        shop_domain=os.environ["SHOPIFY_SHOP_DOMAIN"],
        access_token=os.environ["SHOPIFY_ACCESS_TOKEN"],
        api_version=os.getenv("SHOPIFY_API_VERSION", "2025-10"),
    ):
        payloads = store.products.bulk.set([build_product_with_metafields()])

    for payload in payloads:
        operation = getattr(payload, "productSetOperation", None)
        print(getattr(operation, "id", None), getattr(operation, "status", None))


if __name__ == "__main__":
    main()
