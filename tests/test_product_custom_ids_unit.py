from __future__ import annotations

from typing import cast

from pydantic import ValidationError
import pytest

from shopify_sdk.common.product.custom_ids import (
    ProductCustomIdDefinitionInspection,
    ProductCustomIdDefinitionInspector,
)
from shopify_sdk.gql.core.client import (
    GQLResponse,
    RequestRetryMode,
    ShopifyClient,
    client_context,
)
from shopify_sdk.gql.versions.v2026_07.mutations import productSet
from shopify_sdk.gql.versions.v2026_07.queries import productByIdentifier
from shopify_sdk.gql.versions.v2026_07.types import (
    ProductIdentifierInput,
    ProductSetIdentifiers,
    ProductSetInput,
    UniqueMetafieldValueInput,
)


NAMESPACE = "pikt"
KEY = "external_product_id"
VALUE = "catalog-product-123"


class FakeClient:
    """Return one configured GraphQL payload and retain request metadata."""

    def __init__(self, operation_name: str, payload: dict[str, object]) -> None:
        """Initialize the fake response and request capture state."""
        self.gql_version = "2026-07"
        self._operation_name = operation_name
        self._payload = payload
        self.query: str | None = None
        self.variables: dict[str, object] | None = None
        self.retry_mode: RequestRetryMode | None = None

    def request(
        self,
        query: str,
        variables: dict[str, object] | None = None,
        *,
        retry_mode: RequestRetryMode = RequestRetryMode.NEVER,
    ) -> GQLResponse:
        """Capture the request and return the configured response payload."""
        self.query = query
        self.variables = variables
        self.retry_mode = retry_mode
        return GQLResponse(data={self._operation_name: self._payload})


def custom_id() -> UniqueMetafieldValueInput:
    """Build one valid caller-supplied product custom ID."""
    return UniqueMetafieldValueInput(
        namespace=NAMESPACE,
        key=KEY,
        value=VALUE,
    )


def test_product_by_identifier_builds_and_parses_custom_id_query() -> None:
    """Build custom-ID variables and parse the matching partial product response."""
    query = productByIdentifier(
        identifier=ProductIdentifierInput(customId=custom_id()),
        field_inclusions={"Product": {"id", "handle"}},
    )
    fake_client = FakeClient(
        "productByIdentifier",
        {
            "id": "gid://shopify/Product/1",
            "handle": "example-product",
        },
    )

    product = query.execute(cast(ShopifyClient, fake_client))

    assert query.variables == {
        "identifier": {
            "customId": {
                "namespace": NAMESPACE,
                "key": KEY,
                "value": VALUE,
            }
        }
    }
    assert "$identifier: ProductIdentifierInput!" in query.body
    assert product is not None
    assert product.id == "gid://shopify/Product/1"
    assert product.handle == "example-product"
    assert fake_client.retry_mode is RequestRetryMode.SAFE_READ


def test_product_set_builds_custom_id_identifier() -> None:
    """Render and parse productSet without enabling automatic mutation retries."""
    mutation = productSet(
        input=ProductSetInput(title="Example product"),
        synchronous=True,
        identifier=ProductSetIdentifiers(customId=custom_id()),
        field_inclusions={
            "ProductSetPayload": {"product", "userErrors"},
            "Product": {"id", "handle"},
            "ProductSetUserError": {"code", "field", "message"},
        },
    )

    assert mutation.variables["identifier"] == {
        "customId": {
            "namespace": NAMESPACE,
            "key": KEY,
            "value": VALUE,
        }
    }
    assert mutation.variables["input"] == {"title": "Example product"}
    assert "$identifier: ProductSetIdentifiers" in mutation.body
    assert "identifier: $identifier" in mutation.body

    fake_client = FakeClient(
        "productSet",
        {
            "product": {
                "id": "gid://shopify/Product/1",
                "handle": "example-product",
            },
            "userErrors": [],
        },
    )
    payload = mutation.execute(cast(ShopifyClient, fake_client))

    assert payload.product is not None
    assert payload.product.id == "gid://shopify/Product/1"
    assert fake_client.retry_mode is RequestRetryMode.NEVER


def test_product_set_omits_unspecified_destructive_list_fields() -> None:
    """Keep omitted Shopify list fields absent from productSet variables."""
    mutation = productSet(
        input=ProductSetInput(title="Example product"),
        field_inclusions={"ProductSetPayload": {"userErrors"}},
    )
    variables = mutation.variables

    assert variables["input"] == {"title": "Example product"}
    assert "identifier" not in variables
    assert "identifier" not in mutation.body


def test_product_set_preserves_explicit_empty_lists() -> None:
    """Keep explicit empty lists so callers can intentionally clear Shopify fields."""
    product_input = ProductSetInput(
        title="Example product",
        collections=[],
        files=[],
        metafields=[],
        tags=[],
        variants=[],
    )

    assert product_input.to_graphql() == {
        "title": "Example product",
        "collections": [],
        "files": [],
        "metafields": [],
        "tags": [],
        "variants": [],
    }


@pytest.mark.parametrize(
    "identifier",
    [
        ProductIdentifierInput(id="gid://shopify/Product/1"),
        ProductIdentifierInput(handle="example-product"),
    ],
)
def test_existing_product_identifier_shapes_remain_compatible(
    identifier: ProductIdentifierInput,
) -> None:
    """Preserve existing GID and handle lookup variable shapes."""
    query = productByIdentifier(
        identifier=identifier,
        field_inclusions={"Product": {"id"}},
    )

    assert query.variables["identifier"] in (
        {"id": "gid://shopify/Product/1"},
        {"handle": "example-product"},
    )


def test_custom_id_requires_caller_supplied_namespace_key_and_value() -> None:
    """Reject incomplete custom IDs rather than using hardcoded SDK defaults."""
    with pytest.raises(ValidationError):
        UniqueMetafieldValueInput(key=KEY, value=VALUE)  # type: ignore[call-arg]


def test_read_only_definition_inspector_verifies_custom_id_requirements() -> None:
    """Read and verify owner, namespace, key, type, and unique-values capability."""
    fake_client = FakeClient(
        "metafieldDefinition",
        {
            "id": "gid://shopify/MetafieldDefinition/1",
            "ownerType": "PRODUCT",
            "namespace": NAMESPACE,
            "key": KEY,
            "type": {"name": "id"},
            "capabilities": {
                "uniqueValues": {
                    "eligible": True,
                    "enabled": True,
                }
            },
        },
    )

    with client_context("example.myshopify.com", "token", "2026-07"):
        inspection = ProductCustomIdDefinitionInspector(
            client=cast(ShopifyClient, fake_client)
        ).inspect(namespace=NAMESPACE, key=KEY)

    assert inspection.is_valid is True
    assert inspection.mismatches == ()
    assert fake_client.variables == {
        "identifier": {
            "key": KEY,
            "namespace": NAMESPACE,
            "ownerType": "PRODUCT",
        }
    }
    assert fake_client.retry_mode is RequestRetryMode.SAFE_READ


def test_definition_inspection_reports_requirement_mismatches() -> None:
    """Return stable mismatch codes for an invalid custom-ID definition."""
    inspection = ProductCustomIdDefinitionInspection(
        definition_found=True,
        expected_namespace=NAMESPACE,
        expected_key=KEY,
        owner_type=None,
        namespace="wrong",
        key="wrong",
        type_name="single_line_text_field",
        unique_values_enabled=False,
    )

    assert inspection.is_valid is False
    assert inspection.mismatches == (
        "owner_type_must_be_product",
        "namespace_mismatch",
        "key_mismatch",
        "type_must_be_id",
        "unique_values_must_be_enabled",
    )
