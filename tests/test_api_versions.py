import unittest
from collections.abc import Iterator
from types import SimpleNamespace
from unittest.mock import patch

from shopify_sdk.api_versions import (
    DEFAULT_API_VERSION,
    UnsupportedShopifyApiVersion,
    resolve_api_version,
    version_module_name,
)
from shopify_sdk.gql.core.client import client_context, current_api_version
from shopify_sdk.gql.queries import products
from shopify_sdk.gql.versions.v2025_10.queries import products as Products202510
from shopify_sdk.gql.versions.v2025_10.mutations import productCreate
from shopify_sdk.gql.versions.v2025_10.types import ProductCreateInput
from shopify_sdk.gql.versions.v2025_10.types.objects import Product as Product202510
from shopify_sdk.gql.versions.v2026_07.queries import products as Products202607
from shopify_sdk.gql.versions.v2026_07.types.objects import Product as Product202607


class TestApiVersions(unittest.TestCase):
    def test_default_version_is_latest_supported_version(self) -> None:
        self.assertEqual(DEFAULT_API_VERSION, "2026-07")
        self.assertEqual(resolve_api_version(environ={}), "2026-07")

    def test_env_version_overrides_default(self) -> None:
        self.assertEqual(
            resolve_api_version(environ={"SHOPIFY_API_VERSION": "2025-10"}),
            "2025-10",
        )

    def test_explicit_version_overrides_env(self) -> None:
        self.assertEqual(
            resolve_api_version(
                explicit_version="2026-07",
                environ={"SHOPIFY_API_VERSION": "2025-10"},
            ),
            "2026-07",
        )

    def test_supported_version_module_names(self) -> None:
        self.assertEqual(version_module_name("2025-10"), "v2025_10")
        self.assertEqual(version_module_name("2026-07"), "v2026_07")

    def test_unsupported_version_module_name_raises(self) -> None:
        with self.assertRaises(UnsupportedShopifyApiVersion):
            version_module_name("2024-10")

    def test_query_proxy_uses_active_context_version(self) -> None:
        with client_context("example.myshopify.com", "token", "2025-10"):
            self.assertEqual(current_api_version(), "2025-10")
            self.assertIsInstance(products(), Products202510)

        with client_context("example.myshopify.com", "token", "2026-07"):
            self.assertEqual(current_api_version(), "2026-07")
            self.assertIsInstance(products(), Products202607)

    def test_versioned_product_types_can_diverge(self) -> None:
        self.assertNotIn("bundleConsolidatedOptions", Product202510.model_fields)
        self.assertIn("bundleConsolidatedOptions", Product202607.model_fields)

    def test_versioned_mutation_uses_version_bulk_adapter(self) -> None:
        calls: list[list[object]] = []

        def fake_bulk_mutation(mutations: list[object]) -> Iterator[SimpleNamespace]:
            calls.append(mutations)
            yield SimpleNamespace(
                errors=None,
                data={
                    "productCreate": {
                        "product": {"id": "gid://shopify/Product/1"},
                        "userErrors": [],
                    }
                },
            )

        mutation = productCreate(product=ProductCreateInput(title="Example"))
        with patch(
            "shopify_sdk.gql.versions.v2025_10.bulk.bulk_mutation",
            fake_bulk_mutation,
        ):
            payloads = list(productCreate.bulk([mutation]))

        self.assertEqual(calls, [[mutation]])
        product = getattr(payloads[0], "product")
        self.assertEqual(getattr(product, "id"), "gid://shopify/Product/1")


if __name__ == "__main__":
    unittest.main()
