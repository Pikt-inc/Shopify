import unittest
from types import SimpleNamespace
from unittest.mock import patch

from shopify_sdk.managers.delivery import BulkDeliveryManager, DeliveryManager


class TestBulkDeliveryManager(unittest.TestCase):
    def test_assign_products_batches_and_returns_ids(self) -> None:
        product_ids = ["p1", "p2", "p3"]
        variant_iter = iter(["v1", "v2", "v3"])

        def fake_product_query(*args, **kwargs):
            variant_id = next(variant_iter)
            product = SimpleNamespace(
                variants=SimpleNamespace(nodes=[SimpleNamespace(id=variant_id)])
            )
            return SimpleNamespace(execute=lambda client: product)

        class DummyDeliveryProfileUpdate:
            seen_mutations = None

            def __init__(self, *args, **kwargs) -> None:
                pass

            @classmethod
            def bulk(cls, mutations):
                cls.seen_mutations = mutations
                for _ in mutations:
                    yield SimpleNamespace(userErrors=[])

        manager = BulkDeliveryManager()
        with patch(
            "shopify_sdk.gql.queries.productByIdentifier", new=fake_product_query
        ), patch(
            "shopify_sdk.gql.mutations.deliveryProfileUpdate",
            DummyDeliveryProfileUpdate,
        ):
            result = manager.assign_products(
                profile_id="profile",
                product_ids=product_ids,
                chunk_size=2,
            )

        self.assertEqual(result, product_ids)
        self.assertIsNotNone(DummyDeliveryProfileUpdate.seen_mutations)
        self.assertEqual(len(DummyDeliveryProfileUpdate.seen_mutations), 2)

    def test_assign_products_raises_on_user_errors(self) -> None:
        def fake_product_query(*args, **kwargs):
            product = SimpleNamespace(
                variants=SimpleNamespace(nodes=[SimpleNamespace(id="v1")])
            )
            return SimpleNamespace(execute=lambda client: product)

        class DummyDeliveryProfileUpdate:
            def __init__(self, *args, **kwargs) -> None:
                pass

            @classmethod
            def bulk(cls, mutations):
                yield SimpleNamespace(userErrors=[SimpleNamespace(message="bad")])

        manager = BulkDeliveryManager()
        with patch(
            "shopify_sdk.gql.queries.productByIdentifier", new=fake_product_query
        ), patch(
            "shopify_sdk.gql.mutations.deliveryProfileUpdate",
            DummyDeliveryProfileUpdate,
        ):
            with self.assertRaises(ValueError) as ctx:
                manager.assign_products(profile_id="profile", product_ids=["p1"])

        self.assertIn("Delivery profile assignment failed", str(ctx.exception))


class TestDeliveryManager(unittest.TestCase):
    def test_assign_products_raises_on_payload_none(self) -> None:
        def fake_product_query(*args, **kwargs):
            product = SimpleNamespace(
                variants=SimpleNamespace(nodes=[SimpleNamespace(id="v1")])
            )
            return SimpleNamespace(execute=lambda client: product)

        def fake_delivery_update(*args, **kwargs):
            return SimpleNamespace(execute=lambda client: None)

        manager = DeliveryManager()
        with patch(
            "shopify_sdk.gql.queries.productByIdentifier", new=fake_product_query
        ), patch(
            "shopify_sdk.gql.mutations.deliveryProfileUpdate",
            new=fake_delivery_update,
        ):
            with self.assertRaises(ValueError) as ctx:
                manager.assign_products(profile_id="profile", product_ids=["p1"])

        self.assertIn("Delivery profile assignment failed", str(ctx.exception))
