import unittest
from types import SimpleNamespace
from unittest.mock import patch

from shopify_sdk.gql.mutations import productSet
from shopify_sdk.gql.core.types.enums import ProductStatus, WeightUnit
from shopify_sdk.gql.core.types.input_objects import (
    InventoryItemInput,
    InventoryItemMeasurementInput,
    ProductSetInput,
    ProductVariantSetInput,
    WeightInput,
)


class TestVariantWeightSerialization(unittest.TestCase):
    """productSet serializes nested variant inventoryItem.measurement.weight."""

    def _variables(self, weight_value: float):
        variant = ProductVariantSetInput(
            sku="ABC-123",
            price="49.99",
            inventoryItem=InventoryItemInput(
                measurement=InventoryItemMeasurementInput(
                    weight=WeightInput(unit=WeightUnit.POUNDS, value=weight_value)
                )
            ),
        )
        product = ProductSetInput(
            handle="h1", title="Test", status=ProductStatus.ACTIVE, variants=[variant]
        )
        return productSet(input=product).variables

    def test_weight_is_nested_under_inventory_item_measurement(self) -> None:
        variables = self._variables(25.0)
        variant = variables["input"]["variants"][0]
        self.assertEqual(
            variant["inventoryItem"]["measurement"]["weight"],
            {"unit": "POUNDS", "value": 25.0},
        )

    def test_omitting_inventory_item_leaves_it_null(self) -> None:
        variant = ProductVariantSetInput(sku="NO-WEIGHT", price="1.00")
        product = ProductSetInput(
            handle="h2", title="No weight", variants=[variant]
        )
        variables = productSet(input=product).variables
        # Absent measurement must not emit a weight block.
        self.assertIsNone(variables["input"]["variants"][0].get("inventoryItem"))


class TestVariantQueryWeightSelection(unittest.TestCase):
    """The variant read query selects inventoryItem.measurement.weight."""

    def test_query_all_includes_weight_inclusions(self) -> None:
        import shopify_sdk.managers.variants as variants_mod

        captured: dict = {}

        class FakeQuery:
            def __init__(self, query=None, field_inclusions=None):
                captured["field_inclusions"] = field_inclusions

            def bulk(self):
                return SimpleNamespace(nodes=[])

        with patch.object(variants_mod, "productVariants", FakeQuery):
            variants_mod.ProductVariantManager().query_all(query="tag:x")

        inclusions = captured["field_inclusions"]
        self.assertIn("inventoryItem", inclusions["ProductVariant"])
        self.assertEqual(inclusions["InventoryItem"], {"measurement"})
        self.assertEqual(inclusions["InventoryItemMeasurement"], {"weight"})
        self.assertEqual(inclusions["Weight"], {"value", "unit"})


if __name__ == "__main__":
    unittest.main()
