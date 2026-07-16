from shopify_sdk.gql.core.client import client_context
from shopify_sdk.gql.core.types import (
    ProductIdentifierInput,
    UniqueMetafieldValueInput,
)
from shopify_sdk.gql.queries import draftProductByIdentifier
from shopify_sdk.gql.versions.v2025_10.queries import (
    draftProductByIdentifier as DraftProductByIdentifier202510,
)
from shopify_sdk.gql.versions.v2026_07.queries import (
    draftProductByIdentifier as DraftProductByIdentifier202607,
)


def _identifier() -> ProductIdentifierInput:
    """Return one typed custom product identity."""

    return ProductIdentifierInput(
        customId=UniqueMetafieldValueInput(
            namespace="pikt",
            key="source_product_id",
            value="source:product:1",
        )
    )


def test_draft_product_readback_resolves_active_api_version() -> None:
    """Resolve the query implementation through the active SDK client context."""

    with client_context("example.myshopify.com", "token", "2025-10"):
        query_2025 = draftProductByIdentifier(
            identifier=_identifier(),
            location_id="gid://shopify/Location/1",
        )
    with client_context("example.myshopify.com", "token", "2026-07"):
        query_2026 = draftProductByIdentifier(
            identifier=_identifier(),
            location_id="gid://shopify/Location/1",
        )

    assert isinstance(query_2025, DraftProductByIdentifier202510)
    assert isinstance(query_2026, DraftProductByIdentifier202607)
    assert query_2025.class_name == "productByIdentifier"
    assert query_2026.class_name == "productByIdentifier"


def test_draft_product_readback_owns_safe_typed_projection() -> None:
    """Keep version-specific Shopify field and argument knowledge inside the SDK."""

    with client_context("example.myshopify.com", "token", "2026-07"):
        query = draftProductByIdentifier(
            identifier=_identifier(),
            location_id="gid://shopify/Location/1",
        )

    assert "requiresShipping" not in query.field_inclusions["ProductVariant"]
    assert "requiresShipping" in query.field_inclusions["InventoryItem"]
    assert query.connection_arguments["resourcePublications"] == {
        "first": 250,
        "onlyPublished": False,
    }
    assert query.field_arguments["InventoryItem"]["inventoryLevel"] == {
        "locationId": "gid://shopify/Location/1"
    }
    assert "productByIdentifier(identifier: $identifier)" in query.body
