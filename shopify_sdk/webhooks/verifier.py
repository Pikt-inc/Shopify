from __future__ import annotations

import base64
import binascii
import hashlib
import hmac

from shopify_sdk.webhooks.exceptions import InvalidWebhookSignatureError


class WebhookSignatureVerifier:
    """Verify Shopify HTTPS webhook HMAC signatures using raw request bytes."""

    def __init__(self, app_client_secret: str) -> None:
        """Initialize the verifier with a Shopify app client secret.

        :param app_client_secret: Shopify app client secret used to sign deliveries.
        :raises ValueError: If the secret is blank.
        """
        if not app_client_secret:
            raise ValueError("Webhook app client secret must not be blank.")
        self._app_client_secret = app_client_secret.encode("utf-8")

    def verify(self, raw_body: bytes, hmac_sha256: str) -> None:
        """Validate a base64 HMAC against an unparsed webhook request body.

        :param raw_body: Raw HTTP request bytes before any payload parsing.
        :param hmac_sha256: Base64 HMAC supplied by Shopify.
        :raises InvalidWebhookSignatureError: If the body or signature is invalid.
        """
        if not isinstance(raw_body, bytes):
            raise InvalidWebhookSignatureError("Webhook body must be raw bytes.")
        expected = hmac.new(
            self._app_client_secret,
            raw_body,
            hashlib.sha256,
        ).digest()
        provided = self._decode_signature(hmac_sha256)
        if not hmac.compare_digest(expected, provided):
            raise InvalidWebhookSignatureError("Webhook HMAC signature is invalid.")

    def _decode_signature(self, signature: str) -> bytes:
        """Decode a base64 Shopify HMAC header value.

        :param signature: Base64-encoded HMAC header.
        :returns: Decoded HMAC bytes.
        :raises InvalidWebhookSignatureError: If the header is malformed.
        """
        try:
            return base64.b64decode(signature, validate=True)
        except (TypeError, ValueError, binascii.Error) as exc:
            raise InvalidWebhookSignatureError(
                "Webhook HMAC signature is not valid base64."
            ) from exc
