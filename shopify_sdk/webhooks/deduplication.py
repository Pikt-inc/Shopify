from __future__ import annotations

from typing import Protocol


class WebhookDeliveryStore(Protocol):
    """Application-owned persistence boundary for webhook delivery deduplication."""

    def has_processed(self, webhook_id: str) -> bool:
        """Return whether the delivery ID has already been processed."""

    def mark_processed(self, webhook_id: str) -> None:
        """Persist a delivery ID after successful processing."""
