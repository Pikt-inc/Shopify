import unittest
from types import SimpleNamespace
from unittest.mock import patch

from shopify_sdk.common.product.media import (
    create_product_media,
    delete_product_media,
    set_product_images,
)


class TestProductMedia(unittest.TestCase):
    def test_create_product_media_returns_true_on_empty(self) -> None:
        self.assertTrue(create_product_media("gid://shopify/Product/1", []))

    def test_create_product_media_raises_on_user_errors(self) -> None:
        payload = SimpleNamespace(
            media=[SimpleNamespace(id="gid://shopify/Media/1")],
            mediaUserErrors=[SimpleNamespace(message="bad")],
        )

        def fake_product_create_media(*args, **kwargs):
            return SimpleNamespace(execute=lambda client: payload)

        with patch(
            "shopify_sdk.common.product.media.productCreateMedia",
            new=fake_product_create_media,
        ):
            with self.assertRaises(ValueError) as ctx:
                create_product_media(
                    "gid://shopify/Product/1",
                    ["https://example.com/a.jpg"],
                )

        self.assertIn("Product media creation errors", str(ctx.exception))

    def test_delete_product_media_raises_on_mismatch(self) -> None:
        def fake_file_update(*args, **kwargs):
            return SimpleNamespace(
                execute=lambda client: {"files": [{"id": "gid://shopify/Media/1"}]}
            )

        with patch(
            "shopify_sdk.common.product.media._collect_media_ids",
            return_value=["1", "2"],
        ), patch(
            "shopify_sdk.common.product.media.fileUpdate",
            new=fake_file_update,
        ):
            with self.assertRaises(ValueError) as ctx:
                delete_product_media("gid://shopify/Product/1")

        self.assertIn("Not all product media entries", str(ctx.exception))

    def test_set_product_images_no_update(self) -> None:
        with patch(
            "shopify_sdk.common.product.media.delete_product_media"
        ) as mock_delete, patch(
            "shopify_sdk.common.product.media.create_product_media"
        ) as mock_create:
            self.assertTrue(
                set_product_images("gid://shopify/Product/1", None)
            )

        mock_delete.assert_not_called()
        mock_create.assert_not_called()

    def test_set_product_images_empty_list_clears_only(self) -> None:
        with patch(
            "shopify_sdk.common.product.media.delete_product_media"
        ) as mock_delete, patch(
            "shopify_sdk.common.product.media.create_product_media"
        ) as mock_create:
            self.assertTrue(
                set_product_images("gid://shopify/Product/1", [])
            )

        mock_delete.assert_called_once_with("gid://shopify/Product/1")
        mock_create.assert_not_called()
