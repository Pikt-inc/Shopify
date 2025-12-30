import unittest
from types import SimpleNamespace
from unittest.mock import patch

from shopify_sdk.gql.core.types import ProductCreateInput
from shopify_sdk.managers.products import BulkProductManager, ProductManager


class TestBulkProductManager(unittest.TestCase):
    def test_bulk_create_returns_ids(self) -> None:
        inputs = [
            ProductCreateInput(title="One"),
            ProductCreateInput(title="Two"),
        ]

        class DummyProductCreate:
            def __init__(self, *args, **kwargs) -> None:
                pass

            @classmethod
            def bulk(cls, mutations):
                yield SimpleNamespace(
                    userErrors=[],
                    product=SimpleNamespace(id="gid://shopify/Product/1"),
                )
                yield SimpleNamespace(
                    userErrors=[],
                    product=SimpleNamespace(id="gid://shopify/Product/2"),
                )

        manager = BulkProductManager()
        with patch(
            "shopify_sdk.gql.mutations.productCreate", DummyProductCreate
        ):
            result = manager.create(inputs)

        self.assertEqual(
            result,
            ["gid://shopify/Product/1", "gid://shopify/Product/2"],
        )

    def test_bulk_create_raises_on_user_errors(self) -> None:
        inputs = [ProductCreateInput(title="Bad")]

        class DummyProductCreate:
            def __init__(self, *args, **kwargs) -> None:
                pass

            @classmethod
            def bulk(cls, mutations):
                yield SimpleNamespace(
                    userErrors=[SimpleNamespace(message="nope")],
                    product=None,
                )

        manager = BulkProductManager()
        with patch(
            "shopify_sdk.gql.mutations.productCreate", DummyProductCreate
        ):
            with self.assertRaises(ValueError) as ctx:
                manager.create(inputs)

        self.assertIn("Bulk product creation failed", str(ctx.exception))

    def test_bulk_delete_raises_on_missing_deleted_id(self) -> None:
        class DummyProductDelete:
            def __init__(self, *args, **kwargs) -> None:
                pass

            @classmethod
            def bulk(cls, mutations):
                yield SimpleNamespace(userErrors=[], deletedProductId=None)

        manager = BulkProductManager()
        with patch(
            "shopify_sdk.gql.mutations.productDelete", DummyProductDelete
        ):
            with self.assertRaises(ValueError) as ctx:
                manager.delete(["gid://shopify/Product/1"])

        self.assertIn("Bulk product deletion failed", str(ctx.exception))


class TestProductManager(unittest.TestCase):
    def test_create_calls_set_product_images(self) -> None:
        payload = SimpleNamespace(
            product=SimpleNamespace(id="gid://shopify/Product/1"),
            userErrors=[],
        )

        def fake_product_create(*args, **kwargs):
            return SimpleNamespace(execute=lambda client: payload)

        manager = ProductManager()
        with patch(
            "shopify_sdk.gql.mutations.productCreate", new=fake_product_create
        ), patch(
            "shopify_sdk.common.product.media.set_product_images"
        ) as mock_images:
            product_id = manager.create(
                title="With Images",
                images=["https://example.com/a.jpg"],
            )

        self.assertEqual(product_id, "gid://shopify/Product/1")
        mock_images.assert_called_once_with(
            product_id="gid://shopify/Product/1",
            images=["https://example.com/a.jpg"],
        )

    def test_create_raises_on_user_errors(self) -> None:
        payload = SimpleNamespace(
            product=SimpleNamespace(id="gid://shopify/Product/1"),
            userErrors=[SimpleNamespace(message="bad")],
        )

        def fake_product_create(*args, **kwargs):
            return SimpleNamespace(execute=lambda client: payload)

        manager = ProductManager()
        with patch(
            "shopify_sdk.gql.mutations.productCreate", new=fake_product_create
        ):
            with self.assertRaises(ValueError) as ctx:
                manager.create(title="Bad")

        self.assertIn("Product creation failed", str(ctx.exception))

    def test_delete_raises_on_payload_none(self) -> None:
        def fake_product_delete(*args, **kwargs):
            return SimpleNamespace(execute=lambda client: None)

        manager = ProductManager()
        with patch(
            "shopify_sdk.gql.mutations.productDelete", new=fake_product_delete
        ):
            with self.assertRaises(ValueError) as ctx:
                manager.delete("gid://shopify/Product/1")

        self.assertIn("Product deletion failed", str(ctx.exception))
