import base64
import hashlib
import hmac

import pytest

from shopify_sdk.webhooks import InvalidWebhookPayloadError
from shopify_sdk.webhooks import InvalidWebhookSignatureError
from shopify_sdk.webhooks import MissingWebhookHeaderError
from shopify_sdk.webhooks import WebhookDeliveryParser
from shopify_sdk.webhooks import WebhookHeaderParser
from shopify_sdk.webhooks import WebhookSignatureVerifier


SECRET = "webhook-test-secret"
BODY = b'{"id": 123, "status": "active"}'


def _signature(body: bytes = BODY) -> str:
    digest = hmac.new(SECRET.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("ascii")


def _headers(signature: str | None = None) -> dict[str, str]:
    return {
        "x-shopify-hmac-sha256": signature or _signature(),
        "x-shopify-topic": "products/update",
        "x-shopify-shop-domain": "example.myshopify.com",
        "x-shopify-api-version": "2026-07",
        "x-shopify-webhook-id": "delivery-1",
        "x-shopify-triggered-at": "2026-07-13T12:00:00Z",
        "x-shopify-event-id": "event-1",
        "x-shopify-name": "products-sync",
    }


def test_delivery_parser_verifies_signature_and_normalizes_headers() -> None:
    envelope = WebhookDeliveryParser(SECRET).parse(BODY, _headers())

    assert envelope.payload == {"id": 123, "status": "active"}
    assert envelope.headers.topic == "products/update"
    assert envelope.headers.shop_domain == "example.myshopify.com"
    assert envelope.headers.api_version == "2026-07"
    assert envelope.headers.webhook_id == "delivery-1"
    assert envelope.headers.event_id == "event-1"
    assert envelope.headers.subscription_name == "products-sync"


def test_signature_verifier_rejects_invalid_hmac() -> None:
    with pytest.raises(InvalidWebhookSignatureError):
        WebhookSignatureVerifier(SECRET).verify(BODY, _signature(b"different"))


def test_signature_verifier_rejects_malformed_base64_hmac() -> None:
    with pytest.raises(InvalidWebhookSignatureError, match="base64"):
        WebhookSignatureVerifier(SECRET).verify(BODY, "not-base64!")


def test_delivery_parser_rejects_missing_hmac_header() -> None:
    headers = _headers()
    headers.pop("x-shopify-hmac-sha256")

    with pytest.raises(MissingWebhookHeaderError):
        WebhookDeliveryParser(SECRET).parse(BODY, headers)


def test_signature_verifier_rejects_non_bytes_body() -> None:
    with pytest.raises(InvalidWebhookSignatureError, match="raw bytes"):
        WebhookSignatureVerifier(SECRET).verify("not-raw-bytes", _signature())  # type: ignore[arg-type]


def test_delivery_parser_rejects_verified_non_json_payload() -> None:
    raw_body = b"not json"

    with pytest.raises(InvalidWebhookPayloadError):
        WebhookDeliveryParser(SECRET).parse(raw_body, _headers(_signature(raw_body)))


def test_header_parser_treats_header_names_case_insensitively() -> None:
    headers = WebhookHeaderParser().parse(
        {
            "X-Shopify-Hmac-SHA256": "signature",
            "X-Shopify-Topic": "orders/create",
        }
    )

    assert headers.hmac_sha256 == "signature"
    assert headers.topic == "orders/create"
