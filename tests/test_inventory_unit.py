import unittest
from types import SimpleNamespace
from unittest.mock import patch

from shopify_sdk.common.store.inventory import update_inventory
from shopify_sdk.gql.core.types.input_objects import (
    InventoryAdjustQuantitiesInput,
    InventoryChangeInput,
)
from shopify_sdk.gql.core.types.payload import InventoryAdjustQuantitiesPayload
from shopify_sdk.gql.core.client import client_context
from shopify_sdk.gql.mutations import inventoryAdjustQuantities


class TestInventoryAdjustQuantitiesMutation(unittest.TestCase):
    def test_mutation_declares_typed_payload(self) -> None:
        with client_context("example.myshopify.com", "token", "2026-07"):
            self.assertIs(
                inventoryAdjustQuantities.return_type,
                InventoryAdjustQuantitiesPayload,
            )


class TestUpdateInventoryHelper(unittest.TestCase):
    def _input(self) -> InventoryAdjustQuantitiesInput:
        return InventoryAdjustQuantitiesInput(
            name="available",
            reason="correction",
            changes=[
                InventoryChangeInput(
                    inventoryItemId="gid://shopify/InventoryItem/1",
                    locationId="gid://shopify/Location/1",
                    delta=1,
                )
            ],
        )

    def test_returns_true_when_shopify_has_no_user_errors(self) -> None:
        import shopify_sdk.common.store.inventory as inventory_mod

        class FakeMutation:
            def __init__(self, input):
                self.input = input

            def execute(self, client=None):
                return SimpleNamespace(userErrors=[])

        with patch.object(inventory_mod, "inventoryAdjustQuantities", FakeMutation):
            self.assertTrue(update_inventory(self._input()))

    def test_returns_false_when_shopify_has_user_errors(self) -> None:
        import shopify_sdk.common.store.inventory as inventory_mod

        class FakeMutation:
            def __init__(self, input):
                self.input = input

            def execute(self, client=None):
                return SimpleNamespace(
                    userErrors=[SimpleNamespace(message="inventory failed")]
                )

        with patch.object(inventory_mod, "inventoryAdjustQuantities", FakeMutation):
            self.assertFalse(update_inventory(self._input()))


if __name__ == "__main__":
    unittest.main()
