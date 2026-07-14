from typing import cast
from uuid import UUID

from shopify_sdk.gql.core.bulk.mutation import BulkMutationRunner
from shopify_sdk.gql.core.mutation import Mutation
from shopify_sdk.gql.core.query import Query
from shopify_sdk.gql.versions.v2025_10.mutations import (
    inventorySetQuantities as InventorySetQuantities202510,
)
from shopify_sdk.gql.versions.v2025_10.types import (
    InventoryQuantityInput as InventoryQuantityInput202510,
)
from shopify_sdk.gql.versions.v2025_10.types import (
    InventorySetQuantitiesInput as InventorySetQuantitiesInput202510,
)
from shopify_sdk.gql.versions.v2025_10.types.objects import (
    InventoryLevel as InventoryLevel202510,
)
from shopify_sdk.gql.versions.v2026_07.mutations import (
    inventorySetQuantities as InventorySetQuantities202607,
)
from shopify_sdk.gql.versions.v2026_07.types import (
    InventoryQuantityInput as InventoryQuantityInput202607,
)
from shopify_sdk.gql.versions.v2026_07.types import (
    InventorySetQuantitiesInput as InventorySetQuantitiesInput202607,
)
from shopify_sdk.gql.versions.v2026_07.types.objects import (
    InventoryLevel as InventoryLevel202607,
)


class InventoryLevelQuery202510(Query):
    """Render a 2025-10 inventory level selection for field-argument tests."""

    return_type = InventoryLevel202510


class InventoryLevelQuery202607(Query):
    """Render a 2026-07 inventory level selection for field-argument tests."""

    return_type = InventoryLevel202607


def inventory_field_inclusions() -> dict[str, set[str]]:
    """Return the minimal typed selection needed to read inventory quantity states."""
    return {
        "InventoryLevel": {"quantities"},
        "InventoryQuantity": {"name", "quantity"},
    }


def inventory_field_arguments() -> dict[str, dict[str, dict[str, object]]]:
    """Return required Shopify arguments for InventoryLevel.quantities."""
    return {
        "InventoryLevel": {
            "quantities": {
                "names": ["available", "on_hand"],
            }
        }
    }


def test_inventory_quantities_field_arguments_render_for_both_versions() -> None:
    """Render Shopify's required quantity-state names on a non-connection field."""
    for query_type in (InventoryLevelQuery202510, InventoryLevelQuery202607):
        query = query_type(field_inclusions=inventory_field_inclusions())
        query.with_field_arguments(inventory_field_arguments())

        assert 'quantities(names: ["available", "on_hand"])' in query.fields


def test_2025_inventory_set_quantities_uses_legacy_compare_quantity() -> None:
    """Render the 2025-10 absolute inventory mutation without an idempotency directive."""
    mutation = InventorySetQuantities202510(
        input=InventorySetQuantitiesInput202510(
            name="available",
            reason="correction",
            quantities=[
                InventoryQuantityInput202510(
                    inventoryItemId="gid://shopify/InventoryItem/1",
                    locationId="gid://shopify/Location/1",
                    quantity=10,
                    compareQuantity=8,
                )
            ],
        )
    )

    assert "@idempotent" not in mutation.body
    assert "idempotencyKey" not in mutation.body
    assert mutation.variables["input"]["quantities"] == [
        {
            "inventoryItemId": "gid://shopify/InventoryItem/1",
            "locationId": "gid://shopify/Location/1",
            "quantity": 10,
            "compareQuantity": 8,
        }
    ]


def test_2026_inventory_set_quantities_generates_per_mutation_idempotency_key() -> None:
    """Generate stable per-instance idempotency keys and include explicit CAS nulls."""
    first = InventorySetQuantities202607(
        input=InventorySetQuantitiesInput202607(
            name="available",
            reason="correction",
            quantities=[
                InventoryQuantityInput202607(
                    inventoryItemId="gid://shopify/InventoryItem/1",
                    locationId="gid://shopify/Location/1",
                    quantity=10,
                    changeFromQuantity=None,
                )
            ],
        )
    )
    second = InventorySetQuantities202607(
        input=InventorySetQuantitiesInput202607(
            name="available",
            reason="correction",
            quantities=[
                InventoryQuantityInput202607(
                    inventoryItemId="gid://shopify/InventoryItem/2",
                    locationId="gid://shopify/Location/1",
                    quantity=12,
                    changeFromQuantity=10,
                )
            ],
        )
    )

    UUID(first.idempotencyKey)
    UUID(second.idempotencyKey)
    assert first.idempotencyKey != second.idempotencyKey
    assert first.variables["idempotencyKey"] == first.idempotencyKey
    assert first.variables["input"]["quantities"][0]["changeFromQuantity"] is None
    assert "@idempotent(key: $idempotencyKey)" in first.body
    assert "inventorySetQuantities(input: $input)" in first.body


def test_2026_inventory_set_quantities_bulk_rows_keep_distinct_idempotency_keys() -> None:
    """Serialize a distinct SDK-generated idempotency key beside every bulk JSONL row."""
    mutations = [
        InventorySetQuantities202607(
            input=InventorySetQuantitiesInput202607(
                name="available",
                reason="correction",
                quantities=[
                    InventoryQuantityInput202607(
                        inventoryItemId=f"gid://shopify/InventoryItem/{index}",
                        locationId="gid://shopify/Location/1",
                        quantity=index,
                        changeFromQuantity=None,
                    )
                ],
            )
        )
        for index in (1, 2)
    ]

    variables = BulkMutationRunner(
        mutations=cast(list[Mutation], mutations)
    ).variables

    assert [row["idempotencyKey"] for row in variables] == [
        mutation.idempotencyKey for mutation in mutations
    ]
    assert variables[0]["idempotencyKey"] != variables[1]["idempotencyKey"]
