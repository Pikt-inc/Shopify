from __future__ import annotations

import time
from typing import Any, Iterable

from shopify_sdk.common import ProxyProduct as ProductProxy
from shopify_sdk.tools import run_bulk_query, run_bulk_operation
from shopify_sdk.gql import products, productVariants
from shopify_sdk.gql.mutations import productCreate
from shopify_sdk.gql.core.types import ProductCreateInput, ProductStatus, SEOInput

from shopify_sdk.gql.core.types.objects import Product, ProductVariant
from shopify_sdk.gql.core.types.connections import ProductVariantConnection
PRODUCT_COUNT = 2


def _build_test_products(count: int) -> list[ProductProxy]:
    suffix = int(time.time())
    product_list: list[ProductProxy] = []
    for i in range(count):
        product_list.append(
            ProductProxy(
                sku=f"BULK-TEST-{suffix}-{i}",
                title=f"Bulk Test Product {suffix}-{i}",
                vendor="Bulk Test Vendor",
                type="Bulk Test Type",
                tags=["bulk", "test"],
                price="9.99",
            )
        )
    return product_list


def _product_create_variables(product_list: Iterable[ProductProxy]) -> list[ProductCreateInput]:
    lines: list[ProductCreateInput] = []
    for product in product_list:
        seo = None
        if product.seo_title is not None or product.seo_description is not None:
            seo = SEOInput(
                title=product.seo_title,
                description=product.seo_description,
            )
        create_input = ProductCreateInput(
            title=product.title,
            descriptionHtml=product.description_html,
            vendor=product.vendor,
            productType=product.type,
            tags=product.tags or [],
            status=ProductStatus.ACTIVE,
            seo=seo,
            metafields=product.metafields,
        )
        lines.append(create_input)
    return lines


def _extract_product_id_from_payload(payload: dict[str, Any] | None) -> str | None:
    if not isinstance(payload, dict):
        return None
    product_data = payload.get("product")
    if not isinstance(product_data, dict):
        return None
    product_id = product_data.get("id")
    return product_id if isinstance(product_id, str) else None


def main() -> None:
    product_list = _build_test_products(count=PRODUCT_COUNT)
    variables = _product_create_variables(product_list)

    # # Bulk mutation demo: create products
    results = run_bulk_operation(productCreate, variables, verbose=True)
    print("================ Bulk Mutation Results ================")

    total = 0
    failed = 0
    for index, result in enumerate(results):
        total += 1
        if result.user_errors or result.top_errors:
            failed += 1
            print({"line": result.line_number or total, "userErrors": result.user_errors, "errors": result.top_errors})
            continue

        product_id = _extract_product_id_from_payload(result.payload)
        if index < len(product_list) and product_id:
            product_list[index].id = product_id
        print({"line": result.line_number or total, "product_id": product_id, "result": result.payload})

    # Bulk query demo: fetch all products (ids/titles/status)
    
    bulk_query = productVariants(
        field_exclusions={
            "ProductVariant": ProductVariant.fields_except(
                exclude={"id", "product"}
            ),
            "Product": Product.fields_except(
                exclude={"id"}
            ),
        }
    )
    print("================ Bulk Query Results ================")
    line_count = 0
    lines = []
    for line in run_bulk_query(bulk_query, verbose=True):
        line_count += 1
        lines.append(line)
    print(f"Fetched {line_count} products via bulk query.")
    print(lines[:5])  # Print first 5 products only for brevity
        


if __name__ == "__main__":
    main()
