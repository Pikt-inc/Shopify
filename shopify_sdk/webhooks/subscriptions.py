from __future__ import annotations

from urllib.parse import urlparse

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator


class WebhookSubscriptionCreateRequest(BaseModel):
    """Configuration for a new HTTPS shop-scoped webhook subscription."""

    topic: str
    uri: str
    filter: str | None = Field(default=None)
    include_fields: list[str] = Field(default_factory=list)
    metafield_namespaces: list[str] = Field(default_factory=list)
    name: str | None = Field(default=None)

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, value: str) -> str:
        """Validate that a GraphQL webhook topic value is present."""
        normalized = value.strip()
        if not normalized:
            raise ValueError("Webhook topic must not be blank.")
        return normalized

    @field_validator("uri")
    @classmethod
    def validate_https_uri(cls, value: str) -> str:
        """Validate that v1 subscriptions use an absolute HTTPS endpoint."""
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("Webhook URI must be an absolute HTTPS URL.")
        return value


class WebhookSubscriptionUpdateRequest(BaseModel):
    """Partial configuration update for an HTTPS webhook subscription."""

    id: str
    uri: str | None = Field(default=None)
    filter: str | None = Field(default=None)
    include_fields: list[str] | None = Field(default=None)
    metafield_namespaces: list[str] | None = Field(default=None)
    name: str | None = Field(default=None)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        """Validate that a webhook subscription ID is present."""
        if not value.strip():
            raise ValueError("Webhook subscription ID must not be blank.")
        return value

    @field_validator("uri")
    @classmethod
    def validate_https_uri(cls, value: str | None) -> str | None:
        """Validate an updated endpoint URI when one is supplied."""
        if value is None:
            return None
        return WebhookSubscriptionCreateRequest.validate_https_uri(value)

    @model_validator(mode="after")
    def validate_update_fields(self) -> "WebhookSubscriptionUpdateRequest":
        """Require at least one mutable subscription field in an update request."""
        if "uri" in self.model_fields_set and self.uri is None:
            raise ValueError("Webhook URI cannot be cleared.")
        if self.model_fields_set == {"id"}:
            raise ValueError("Webhook update requires at least one changed field.")
        return self


class WebhookSubscriptionListRequest(BaseModel):
    """Filter and pagination settings for API-created webhook subscriptions."""

    first: int = Field(default=100, ge=1, le=250)
    after: str | None = Field(default=None)
    topics: list[str] | None = Field(default=None)
    uri: str | None = Field(default=None)
    query: str | None = Field(default=None)
    reverse: bool = Field(default=False)


class WebhookSubscriptionUserError(BaseModel):
    """A structured Shopify user error from a webhook subscription operation."""

    field: list[str] | None = Field(default=None)
    message: str
