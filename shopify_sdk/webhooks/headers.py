from __future__ import annotations

from collections.abc import Mapping

from shopify_sdk.webhooks.models import WebhookHeaders


class WebhookHeaderParser:
    """Parse Shopify webhook headers without depending on a web framework."""

    def parse(self, headers: Mapping[str, str]) -> WebhookHeaders:
        """Return normalized webhook metadata from case-insensitive headers.

        :param headers: Incoming HTTP headers from the framework boundary.
        :returns: Parsed Shopify webhook headers.
        """
        values = {str(name).casefold(): str(value) for name, value in headers.items()}
        return WebhookHeaders(
            hmac_sha256=values.get("x-shopify-hmac-sha256"),
            topic=values.get("x-shopify-topic"),
            shop_domain=values.get("x-shopify-shop-domain"),
            api_version=values.get("x-shopify-api-version"),
            webhook_id=values.get("x-shopify-webhook-id"),
            triggered_at=values.get("x-shopify-triggered-at"),
            event_id=values.get("x-shopify-event-id"),
            subscription_name=values.get("x-shopify-name"),
        )
