from shopify_sdk.gql.core.types.input_objects import (
    InventoryAdjustQuantitiesInput,
)
from shopify_sdk.gql.mutations import inventoryAdjustQuantities
from shopify_sdk import client


def update_inventory(input: InventoryAdjustQuantitiesInput) -> bool:
    result = inventoryAdjustQuantities(input=input).execute(client=client)

    if result and result.get("userErrors") == []:
        return True
    return False
