from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field


class WebhookHeaders(BaseModel):
    """Normalized metadata from Shopify webhook delivery headers."""

    hmac_sha256: str | None = Field(default=None)
    topic: str | None = Field(default=None)
    shop_domain: str | None = Field(default=None)
    api_version: str | None = Field(default=None)
    webhook_id: str | None = Field(default=None)
    triggered_at: str | None = Field(default=None)
    event_id: str | None = Field(default=None)
    subscription_name: str | None = Field(default=None)


class WebhookEnvelope(BaseModel):
    """A verified Shopify webhook delivery and its generic JSON payload."""

    headers: WebhookHeaders
    raw_body: bytes
    payload: dict[str, object] | list[object]
