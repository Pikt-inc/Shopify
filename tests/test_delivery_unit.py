import unittest
from types import SimpleNamespace
from unittest.mock import patch

from shopify_sdk.gql.core.types.input_objects import DeliveryProfileInput
from shopify_sdk.managers.delivery import DeliveryProfileManager


class DummyDeliveryProfileUpdateSuccess:
    seen_mutations = None

    def __init__(self, *args, **kwargs) -> None:
        self.kwargs = kwargs

    @classmethod
    def bulk(cls, mutations):
        cls.seen_mutations = mutations
        for _ in mutations:
            yield SimpleNamespace(userErrors=[])


class DummyDeliveryProfileUpdateUserError:
    def __init__(self, *args, **kwargs) -> None:
        pass

    @classmethod
    def bulk(cls, mutations):
        for _ in mutations:
            yield SimpleNamespace(userErrors=[SimpleNamespace(message="bad")])


class DummyDeliveryProfileCreateUserError:
    def __init__(self, *args, **kwargs) -> None:
        pass

    @classmethod
    def bulk(cls, mutations):
        for _ in mutations:
            yield SimpleNamespace(userErrors=[SimpleNamespace(message="nope")])


class TestDeliveryProfileManager(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = DeliveryProfileManager()
        self.product_id = "prod-123"
        self.rate = 9.99
        self.fake_store = SimpleNamespace(
            products=SimpleNamespace(
                bulk=SimpleNamespace(product_variant_map={self.product_id: ["var-1"]})
            )
        )
        self._profiles_patcher = patch.object(
            DeliveryProfileManager, "profiles", return_value=SimpleNamespace(nodes=[])
        )
        self._details_patcher = patch.object(
            DeliveryProfileManager,
            "details",
            return_value=SimpleNamespace(id="profile-1", profileLocationGroups=[]),
        )
        self._profiles_patcher.start()
        self._details_patcher.start()

    def tearDown(self) -> None:
        self._profiles_patcher.stop()
        self._details_patcher.stop()

    def test_set_associates_variants_and_returns_true(self) -> None:
        DummyDeliveryProfileUpdateSuccess.seen_mutations = None
        with (
            patch.object(
                DeliveryProfileManager,
                "_get_rate_to_variant_id_map",
                return_value={self.rate: ["var-1"]},
            ),
            patch.object(
                DeliveryProfileManager,
                "_get_missing_rates",
                return_value=[],
            ),
            patch.object(
                DeliveryProfileManager,
                "_bulk_create_flat_rate_shipping_profile",
            ),
            patch.object(
                DeliveryProfileManager,
                "profiles",
                return_value=SimpleNamespace(nodes=[]),
            ),
            patch.object(
                DeliveryProfileManager,
                "rate_to_delivery_profile",
                return_value={self.rate: "profile-1"},
            ),
            patch(
                "shopify_sdk.managers.delivery.DeliveryProfileInput",
                DeliveryProfileInput,
                create=True,
            ),
            patch(
                "shopify_sdk.managers.delivery.deliveryProfileUpdate",
                DummyDeliveryProfileUpdateSuccess,
            ),
        ):
            result = self.manager.set([(self.product_id, self.rate)])

        self.assertTrue(result)
        self.assertIsNotNone(DummyDeliveryProfileUpdateSuccess.seen_mutations)
        assert DummyDeliveryProfileUpdateSuccess.seen_mutations is not None
        mutation = DummyDeliveryProfileUpdateSuccess.seen_mutations[0]
        self.assertEqual(mutation.kwargs["id"], "profile-1")
        self.assertEqual(
            mutation.kwargs["profile"].variantsToAssociate,
            ["var-1"],
        )

    def test_set_raises_when_user_errors_in_bulk(self) -> None:
        with (
            patch.object(
                DeliveryProfileManager,
                "_get_rate_to_variant_id_map",
                return_value={self.rate: ["var-1"]},
            ),
            patch.object(
                DeliveryProfileManager,
                "_get_missing_rates",
                return_value=[],
            ),
            patch.object(
                DeliveryProfileManager,
                "_bulk_create_flat_rate_shipping_profile",
            ),
            patch.object(
                DeliveryProfileManager,
                "profiles",
                return_value=SimpleNamespace(nodes=[]),
            ),
            patch.object(
                DeliveryProfileManager,
                "rate_to_delivery_profile",
                return_value={self.rate: "profile-1"},
            ),
            patch(
                "shopify_sdk.managers.delivery.DeliveryProfileInput",
                DeliveryProfileInput,
                create=True,
            ),
            patch(
                "shopify_sdk.managers.delivery.deliveryProfileUpdate",
                DummyDeliveryProfileUpdateUserError,
            ),
        ):
            with self.assertRaises(ValueError) as ctx:
                self.manager.set([(self.product_id, self.rate)])

        self.assertIn("Delivery profile assignment failed", str(ctx.exception))

    def test_get_rate_to_variant_id_map_aggregates_variants_for_same_rate(self) -> None:
        variant_map = {
            "prod-1": ["var-1"],
            "prod-2": ["var-2"],
            "prod-3": ["var-3"],
        }

        fake_store = SimpleNamespace(
            products=SimpleNamespace(
                bulk=SimpleNamespace(product_variant_map=variant_map)
            )
        )
        with patch("shopify_sdk.managers.delivery._get_store", return_value=fake_store):
            rate_map = self.manager._get_rate_to_variant_id_map(
                input=[
                    ("prod-1", 5.0),
                    ("prod-2", 5.0),
                    ("prod-3", 7.5),
                ]
            )

        self.assertEqual(rate_map[5.0], ["var-1", "var-2"])
        self.assertEqual(rate_map[7.5], ["var-3"])

    def test_set_handles_multiple_products_creating_multiple_profiles(self) -> None:
        entries = [
            ("prod-1", 10.0),
            ("prod-2", 10.0),
            ("prod-3", 15.5),
            ("prod-4", 15.5),
            ("prod-5", 20.0),
        ]
        unique_rates = {10.0, 15.5, 20.0}
        DummyDeliveryProfileUpdateSuccess.seen_mutations = None

        created_rate_calls: list[list[float]] = []

        def capture_bulk_creation(rate_prices):
            created_rate_calls.append(list(rate_prices))

        with (
            patch.object(
                DeliveryProfileManager,
                "_get_rate_to_variant_id_map",
                return_value={
                    10.0: ["var-1", "var-2"],
                    15.5: ["var-3", "var-4"],
                    20.0: ["var-5"],
                },
            ),
            patch.object(
                DeliveryProfileManager,
                "_get_missing_rates",
                return_value=[10.0, 15.5, 20.0, 15.5],
            ),
            patch.object(
                DeliveryProfileManager,
                "_bulk_create_flat_rate_shipping_profile",
                side_effect=capture_bulk_creation,
            ),
            patch.object(
                DeliveryProfileManager,
                "rate_to_delivery_profile",
                return_value={
                    10.0: "profile-10",
                    15.5: "profile-15",
                    20.0: "profile-20",
                },
            ),
            patch(
                "shopify_sdk.managers.delivery.DeliveryProfileInput",
                DeliveryProfileInput,
                create=True,
            ),
            patch(
                "shopify_sdk.managers.delivery.deliveryProfileUpdate",
                DummyDeliveryProfileUpdateSuccess,
            ),
        ):
            result = self.manager.set(entries)

        self.assertTrue(result)
        self.assertEqual(len(created_rate_calls), 1)
        self.assertSetEqual(set(created_rate_calls[0]), unique_rates)
        mutations: list[object] = DummyDeliveryProfileUpdateSuccess.seen_mutations or []
        self.assertEqual(len(mutations), len(entries))

    def test_set_assigns_variants_for_distinct_rates_in_one_call(self) -> None:
        entries = [
            ("prod-A", 5.0),
            ("prod-B", 7.0),
            ("prod-C", 9.25),
            ("prod-D", 12.5),
        ]
        rate_variants = {
            5.0: ["var-A"],
            7.0: ["var-B"],
            9.25: ["var-C1", "var-C2"],
            12.5: ["var-D"],
        }
        captured_creation: list[list[float]] = []

        def capture_bulk_creation(rate_prices):
            captured_creation.append(list(rate_prices))

        with (
            patch.object(
                DeliveryProfileManager,
                "_get_rate_to_variant_id_map",
                return_value=rate_variants,
            ),
            patch.object(
                DeliveryProfileManager,
                "_get_missing_rates",
                return_value=list(rate_variants.keys()),
            ),
            patch.object(
                DeliveryProfileManager,
                "_bulk_create_flat_rate_shipping_profile",
                side_effect=capture_bulk_creation,
            ),
            patch.object(
                DeliveryProfileManager,
                "profiles",
                return_value=SimpleNamespace(nodes=[]),
            ),
            patch.object(
                DeliveryProfileManager,
                "rate_to_delivery_profile",
                return_value={rate: f"profile-{rate}" for rate in rate_variants},
            ),
            patch(
                "shopify_sdk.managers.delivery.DeliveryProfileInput",
                DeliveryProfileInput,
                create=True,
            ),
            patch(
                "shopify_sdk.managers.delivery.deliveryProfileUpdate",
                DummyDeliveryProfileUpdateSuccess,
            ),
        ):
            self.manager.set(entries)

        self.assertEqual(len(captured_creation), 1)
        self.assertSetEqual(set(captured_creation[0]), set(rate_variants.keys()))
        mutations: list[object] = DummyDeliveryProfileUpdateSuccess.seen_mutations or []
        self.assertEqual(len(mutations), len(entries))

    def test_set_skips_rates_without_variant_ids(self) -> None:
        entries = [("prod-1", 5.0)]
        DummyDeliveryProfileUpdateSuccess.seen_mutations = None

        with (
            patch.object(
                DeliveryProfileManager,
                "_get_rate_to_variant_id_map",
                return_value={5.0: []},
            ),
            patch.object(
                DeliveryProfileManager,
                "_get_missing_rates",
                return_value=[],
            ),
            patch.object(
                DeliveryProfileManager,
                "_bulk_create_flat_rate_shipping_profile",
            ),
            patch.object(
                DeliveryProfileManager,
                "profiles",
                return_value=SimpleNamespace(nodes=[]),
            ),
            patch.object(
                DeliveryProfileManager,
                "rate_to_delivery_profile",
                return_value={5.0: "profile-empty"},
            ),
            patch(
                "shopify_sdk.managers.delivery.DeliveryProfileInput",
                DeliveryProfileInput,
                create=True,
            ),
            patch(
                "shopify_sdk.managers.delivery.deliveryProfileUpdate",
                DummyDeliveryProfileUpdateSuccess,
            ),
            patch(
                "shopify_sdk.managers.delivery.logger.warning",
            ) as mock_warning,
        ):
            result = self.manager.set(entries)

        self.assertTrue(result)
        self.assertEqual(DummyDeliveryProfileUpdateSuccess.seen_mutations, [])
        mock_warning.assert_called_with(
            "No variants found for rate '%s' during shipping profile setup.",
            5.0,
        )

    def test_set_raises_when_rate_lacks_profile_mapping(self) -> None:
        entries = [("prod-1", 8.0)]
        with (
            patch.object(
                DeliveryProfileManager,
                "_get_rate_to_variant_id_map",
                return_value={8.0: ["var-1"]},
            ),
            patch.object(
                DeliveryProfileManager,
                "_get_missing_rates",
                return_value=[],
            ),
            patch.object(
                DeliveryProfileManager,
                "_bulk_create_flat_rate_shipping_profile",
            ),
            patch.object(
                DeliveryProfileManager,
                "profiles",
                return_value=SimpleNamespace(nodes=[]),
            ),
            patch.object(
                DeliveryProfileManager,
                "rate_to_delivery_profile",
                return_value={},
            ),
            patch(
                "shopify_sdk.managers.delivery.DeliveryProfileInput",
                DeliveryProfileInput,
                create=True,
            ),
            patch(
                "shopify_sdk.managers.delivery.deliveryProfileUpdate",
                DummyDeliveryProfileUpdateSuccess,
            ),
        ):
            with self.assertRaises(ValueError) as ctx:
                self.manager.set(entries)

        self.assertIn(
            "Delivery profile for rate '8.0' was not found", str(ctx.exception)
        )

    def test_bulk_create_raises_on_user_errors(self) -> None:
        fake_store = SimpleNamespace(location_ids=["loc-1"])
        with (
            patch("shopify_sdk.managers.delivery._get_store", return_value=fake_store),
            patch(
                "shopify_sdk.managers.delivery.deliveryProfileCreate",
                DummyDeliveryProfileCreateUserError,
            ),
        ):
            with self.assertRaises(ValueError) as ctx:
                self.manager._bulk_create_flat_rate_shipping_profile([5.0])

        self.assertIn("Delivery profile creation failed", str(ctx.exception))
