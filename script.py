from __future__ import annotations

import time
from typing import Iterable

from shopify_sdk.common import ProxyProduct as ProductProxy
from shopify_sdk.common.product import product_by_sku
from shopify_sdk.managers.store import StoreManager

PRODUCT_COUNT = 2


def _build_test_products(count: int) -> list[ProductProxy]:
    suffix = int(time.time())
    product_list: list[ProductProxy] = []
    for i in range(count):
        p = ProductProxy(
            sku=f"BULK-TEST-{suffix}-{i}",
            title=f"Bulk Test Product {suffix}-{i}",
            vendor="Bulk Test Vendor",
            type="Bulk Test Type",
            tags=["bulk", "test"],
            price="9.99",
            quantity=1,
            seo_description="SEO Description for Bulk Test Product",
            seo_title="SEO Title for Bulk Test Product",
        )
        p.add_metafield(
            namespace="pikt",
            key="compatibility",
            type=ProductProxy.metafield_type.JSON,
            value="{\"devices\": [\"iOS\", \"Android\"]}"
        )
        product_list.append(p)
    return product_list


def _lookup_product_id_by_sku(sku: str, retries: int = 3, delay_s: float = 2.0) -> str:
    # Bulk mutations can take a moment to surface in query APIs, so retry briefly.
    for attempt in range(retries):
        try:
            return product_by_sku(sku).id
        except Exception:
            if attempt >= retries - 1:
                raise
            time.sleep(delay_s)
    raise ValueError(f"Failed to resolve product ID for SKU '{sku}'")


def _populate_product_ids(product_list: Iterable[ProductProxy]) -> None:
    for product in product_list:
        if not product.sku:
            raise ValueError("Each product must have a SKU to resolve its ID after create.")
        product.id = _lookup_product_id_by_sku(product.sku)


def _build_update_products(product_list: Iterable[ProductProxy]) -> list[ProductProxy]:
    updated_products: list[ProductProxy] = []
    for product in product_list:
        if not product.id:
            raise ValueError("Each product must have an 'id' for bulk update.")
        tags = list(product.tags or [])
        if "bulk-update" not in tags:
            tags.append("bulk-update")
        updated_products.append(
            ProductProxy(
                id=product.id,
                sku=product.sku,
                title=f"{product.title} (Updated)",
                vendor=product.vendor,
                type=product.type,
                tags=tags,
                description_html=product.description_html,
                seo_title=product.seo_title,
                seo_description=product.seo_description,
                metafields=product.metafields,
            )
        )
    return updated_products


def main() -> None:
    store = StoreManager()
    product_list = _build_test_products(count=PRODUCT_COUNT)

    success = store.products.bulk.set(product_list)
    if not success:
        print("Bulk set failed.")
        return
    print(product_list[10])
    product = product_list[10]
    product.hydrate()
    print(product)
    
    # for p in product_list:
    #     print(f"  ✓ Created product SKU: {p.sku} with ID: {p.id}")

    # print(f"Bulk create succeeded: {created}")

    # _populate_product_ids(product_list)
    # update_products = _build_update_products(product_list)
    # print(f"Prepared {len(update_products)} products for bulk update.", update_products[0])

    # updated = store.products.bulk.set(update_products)
    # print(f"Bulk update succeeded: {updated}")


if __name__ == "__main__":
    main()
