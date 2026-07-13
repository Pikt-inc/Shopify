from __future__ import annotations

import json
from collections.abc import Mapping

from shopify_sdk.webhooks.exceptions import InvalidWebhookPayloadError
from shopify_sdk.webhooks.exceptions import MissingWebhookHeaderError
from shopify_sdk.webhooks.headers import WebhookHeaderParser
from shopify_sdk.webhooks.models import WebhookEnvelope
from shopify_sdk.webhooks.verifier import WebhookSignatureVerifier


class WebhookDeliveryParser:
    """Verify and parse raw Shopify HTTPS webhook deliveries."""

    def __init__(self, app_client_secret: str) -> None:
        """Initialize delivery parsing with a Shopify app client secret.

        :param app_client_secret: Shopify app client secret used to sign deliveries.
        """
        self._header_parser = WebhookHeaderParser()
        self._signature_verifier = WebhookSignatureVerifier(app_client_secret)

    def parse(self, raw_body: bytes, headers: Mapping[str, str]) -> WebhookEnvelope:
        """Verify headers and parse the JSON body of a webhook delivery.

        :param raw_body: Raw request bytes before any payload parsing.
        :param headers: Incoming HTTP headers from the framework boundary.
        :returns: Verified delivery envelope with normalized metadata and payload.
        :raises MissingWebhookHeaderError: If the HMAC header is missing.
        :raises InvalidWebhookPayloadError: If verified bytes are not JSON object/list data.
        """
        parsed_headers = self._header_parser.parse(headers)
        if not parsed_headers.hmac_sha256:
            raise MissingWebhookHeaderError("Missing X-Shopify-Hmac-Sha256 header.")
        self._signature_verifier.verify(raw_body, parsed_headers.hmac_sha256)
        return WebhookEnvelope(
            headers=parsed_headers,
            raw_body=raw_body,
            payload=self._parse_payload(raw_body),
        )

    def _parse_payload(self, raw_body: bytes) -> dict[str, object] | list[object]:
        """Parse a verified JSON object or list webhook payload.

        :param raw_body: Verified raw webhook request bytes.
        :returns: Decoded JSON object or list.
        :raises InvalidWebhookPayloadError: If payload JSON is invalid or scalar.
        """
        try:
            payload = json.loads(raw_body)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InvalidWebhookPayloadError("Webhook body is not valid JSON.") from exc
        if not isinstance(payload, (dict, list)):
            raise InvalidWebhookPayloadError(
                "Webhook JSON payload must be an object or list."
            )
        return payload
