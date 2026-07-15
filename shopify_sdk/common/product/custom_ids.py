"""Read-only inspection for Shopify product custom-ID metafield definitions."""

from typing import cast

from pydantic import BaseModel, ConfigDict

from shopify_sdk import client as default_client
from shopify_sdk.gql.core.client import ShopifyClient
from shopify_sdk.gql.core.types import (
    MetafieldDefinition,
    MetafieldDefinitionIdentifierInput,
    MetafieldOwnerType,
)
from shopify_sdk.gql.queries import metafieldDefinition


class ProductCustomIdDefinitionInspection(BaseModel):
    """Typed verification result for a product custom-ID metafield definition."""

    definition_found: bool
    expected_namespace: str
    expected_key: str
    owner_type: MetafieldOwnerType | None = None
    namespace: str | None = None
    key: str | None = None
    type_name: str | None = None
    unique_values_enabled: bool = False
    model_config = ConfigDict(frozen=True)

    @property
    def is_valid(self) -> bool:
        """Return whether the definition satisfies Shopify custom-ID requirements."""
        return not self.mismatches

    @property
    def mismatches(self) -> tuple[str, ...]:
        """Return stable mismatch codes for failed definition requirements."""
        if not self.definition_found:
            return ("definition_not_found",)
        mismatches: list[str] = []
        if self.owner_type is not MetafieldOwnerType.PRODUCT:
            mismatches.append("owner_type_must_be_product")
        if self.namespace != self.expected_namespace:
            mismatches.append("namespace_mismatch")
        if self.key != self.expected_key:
            mismatches.append("key_mismatch")
        if self.type_name != "id":
            mismatches.append("type_must_be_id")
        if not self.unique_values_enabled:
            mismatches.append("unique_values_must_be_enabled")
        return tuple(mismatches)

    @classmethod
    def from_definition(
        cls,
        definition: MetafieldDefinition | None,
        *,
        namespace: str,
        key: str,
    ) -> "ProductCustomIdDefinitionInspection":
        """Build a verification result from an optional Shopify definition."""
        if definition is None:
            return cls(
                definition_found=False,
                expected_namespace=namespace,
                expected_key=key,
            )
        return cls(
            definition_found=True,
            expected_namespace=namespace,
            expected_key=key,
            owner_type=definition.ownerType,
            namespace=definition.namespace,
            key=definition.key,
            type_name=definition.type.name,
            unique_values_enabled=definition.capabilities.uniqueValues.enabled,
        )


class ProductCustomIdDefinitionInspector:
    """Read and verify one Shopify product custom-ID metafield definition."""

    def __init__(self, client: ShopifyClient | None = None) -> None:
        """Initialize with an optional explicit Shopify client."""
        self._client = client or cast(ShopifyClient, default_client)

    def inspect(
        self,
        *,
        namespace: str,
        key: str,
    ) -> ProductCustomIdDefinitionInspection:
        """Read and verify a product custom-ID definition without mutating Shopify."""
        if self._client.gql_version != "2026-07":
            raise ValueError(
                "Product custom-ID definition inspection requires API version 2026-07."
            )
        identifier = MetafieldDefinitionIdentifierInput(
            ownerType=MetafieldOwnerType.PRODUCT,
            namespace=namespace,
            key=key,
        )
        definition = metafieldDefinition(identifier=identifier).execute(self._client)
        return ProductCustomIdDefinitionInspection.from_definition(
            definition,
            namespace=namespace,
            key=key,
        )
