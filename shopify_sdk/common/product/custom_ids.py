"""Inspect and explicitly create Shopify product custom-ID definitions."""

from typing import Self, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator

from shopify_sdk import client as default_client
from shopify_sdk.gql.core.client import ShopifyClient
from shopify_sdk.gql.core.types import (
    MetafieldDefinition,
    MetafieldDefinitionIdentifierInput,
    MetafieldDefinitionInput,
    MetafieldOwnerType,
)
from shopify_sdk.gql.mutations import metafieldDefinitionCreate
from shopify_sdk.gql.queries import metafieldDefinition


class ProductCustomIdDefinitionInspection(BaseModel):
    """Typed verification result for a product custom-ID metafield definition."""

    definition_found: bool
    definition_id: str | None = None
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
                definition_id=None,
                expected_namespace=namespace,
                expected_key=key,
            )
        return cls(
            definition_found=True,
            definition_id=definition.id,
            expected_namespace=namespace,
            expected_key=key,
            owner_type=definition.ownerType,
            namespace=definition.namespace,
            key=definition.key,
            type_name=definition.type.name,
            unique_values_enabled=definition.capabilities.uniqueValues.enabled,
        )

    @model_validator(mode="after")
    def validate_definition_identity(self) -> Self:
        """Require found definitions to retain their Shopify GID."""

        if self.definition_found != (self.definition_id is not None):
            raise ValueError("definition presence must agree with its Shopify GID")
        return self


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


class ProductCustomIdDefinitionCreateUserError(BaseModel):
    """Stable structured user error from Shopify definition creation."""

    code: str | None = None
    field: tuple[str, ...] | None = None
    message: str = Field(min_length=1)
    model_config = ConfigDict(frozen=True)


class ProductCustomIdDefinitionCreateResult(BaseModel):
    """Typed outcome of one explicit non-retrying definition mutation."""

    created_definition_id: str | None = None
    user_errors: tuple[ProductCustomIdDefinitionCreateUserError, ...] = ()
    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def validate_outcome(self) -> Self:
        """Require a created definition or structured Shopify errors."""

        if self.created_definition_id is None and not self.user_errors:
            raise ValueError("Shopify definition creation returned no outcome")
        return self


class ProductCustomIdDefinitionCreator:
    """Create one exact product custom-ID definition without retries."""

    def __init__(self, client: ShopifyClient | None = None) -> None:
        """Initialize with an optional explicit Shopify client."""

        self._client = client or cast(ShopifyClient, default_client)

    def create(
        self,
        *,
        name: str,
        namespace: str,
        key: str,
    ) -> ProductCustomIdDefinitionCreateResult:
        """Create one exact ``PRODUCT`` definition of Shopify type ``id``."""

        if self._client.gql_version != "2026-07":
            raise ValueError(
                "Product custom-ID definition creation requires API version 2026-07."
            )
        definition = MetafieldDefinitionInput(
            name=name,
            namespace=namespace,
            key=key,
            ownerType=MetafieldOwnerType.PRODUCT,
            type="id",
        )
        payload = metafieldDefinitionCreate(definition=definition).execute(self._client)
        created = payload.createdDefinition
        return ProductCustomIdDefinitionCreateResult(
            created_definition_id=created.id if created is not None else None,
            user_errors=tuple(
                ProductCustomIdDefinitionCreateUserError(
                    code=error.code,
                    field=tuple(error.field) if error.field is not None else None,
                    message=error.message,
                )
                for error in payload.userErrors
            ),
        )


__all__ = [
    "ProductCustomIdDefinitionCreateResult",
    "ProductCustomIdDefinitionCreateUserError",
    "ProductCustomIdDefinitionCreator",
    "ProductCustomIdDefinitionInspection",
    "ProductCustomIdDefinitionInspector",
]
