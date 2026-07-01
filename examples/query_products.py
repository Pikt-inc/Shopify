"""Query active Shopify products with the manager API."""

from __future__ import annotations

import os

from shopify_sdk import store


def main() -> None:
    """Print active product identifiers from the configured Shopify store."""

    with store.credentials_context(
        shop_domain=os.environ["SHOPIFY_SHOP_DOMAIN"],
        access_token=os.environ["SHOPIFY_ACCESS_TOKEN"],
        api_version=os.getenv("SHOPIFY_API_VERSION", "2025-10"),
    ):
        products = store.products.query_all(query="status:active")

    for product in products.nodes:
        print(product.id, product.handle, product.title)


if __name__ == "__main__":
    main()
