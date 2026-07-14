import os
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from shopify_sdk.gql.core.client import ShopifyRetryPolicy
from shopify_sdk.managers.store import StoreManager


class TestStoreManager(unittest.TestCase):
    def test_credentials_context_uses_default_version(self) -> None:
        calls = []

        @contextmanager
        def fake_client_context(**kwargs):
            calls.append(kwargs)
            yield object()

        manager = StoreManager()
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("shopify_sdk.client_context", fake_client_context),
        ):
            with manager.credentials_context(
                shop_domain="example.myshopify.com",
                access_token="token",
            ) as ctx:
                self.assertIs(ctx, manager)

        self.assertEqual(calls[0]["api_version"], "2026-07")

    def test_credentials_context_prefers_env_version(self) -> None:
        calls = []

        @contextmanager
        def fake_client_context(**kwargs):
            calls.append(kwargs)
            yield object()

        manager = StoreManager()
        with (
            patch.dict(os.environ, {"SHOPIFY_API_VERSION": "2024-10"}),
            patch("shopify_sdk.client_context", fake_client_context),
        ):
            with manager.credentials_context(
                shop_domain="example.myshopify.com",
                access_token="token",
            ):
                pass

        self.assertEqual(calls[0]["api_version"], "2024-10")

    def test_credentials_context_overrides_env_version(self) -> None:
        calls = []

        @contextmanager
        def fake_client_context(**kwargs):
            calls.append(kwargs)
            yield object()

        manager = StoreManager()
        with (
            patch.dict(os.environ, {"SHOPIFY_API_VERSION": "2024-10"}),
            patch("shopify_sdk.client_context", fake_client_context),
        ):
            with manager.credentials_context(
                shop_domain="example.myshopify.com",
                access_token="token",
                api_version="2023-07",
            ):
                pass

        self.assertEqual(calls[0]["api_version"], "2023-07")

    def test_credentials_context_passes_retry_policy(self) -> None:
        """Pass an explicit safe-read retry policy to the active client context."""
        calls = []
        retry_policy = ShopifyRetryPolicy(max_attempts=1)

        @contextmanager
        def fake_client_context(**kwargs):
            calls.append(kwargs)
            yield object()

        manager = StoreManager()
        with patch("shopify_sdk.client_context", fake_client_context):
            with manager.credentials_context(
                shop_domain="example.myshopify.com",
                access_token="token",
                retry_policy=retry_policy,
            ):
                pass

        assert calls[0]["retry_policy"] is retry_policy
