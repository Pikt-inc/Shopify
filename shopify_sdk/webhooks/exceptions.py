from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shopify_sdk.webhooks.subscriptions import WebhookSubscriptionUserError


class WebhookError(Exception):
    """Base exception for SDK webhook operations."""


class WebhookVerificationError(WebhookError):
    """Raised when an incoming webhook delivery cannot be verified."""


class MissingWebhookHeaderError(WebhookVerificationError):
    """Raised when a required webhook delivery header is absent."""


class InvalidWebhookSignatureError(WebhookVerificationError):
    """Raised when a webhook HMAC signature is invalid."""


class InvalidWebhookPayloadError(WebhookVerificationError):
    """Raised when a verified webhook body is not valid JSON payload data."""


class UnsupportedWebhookApiVersion(WebhookError):
    """Raised when subscription management lacks an API-version implementation."""


class WebhookSubscriptionError(WebhookError):
    """Raised when Shopify rejects a webhook subscription operation."""

    def __init__(
        self,
        operation: str,
        user_errors: list[WebhookSubscriptionUserError],
    ) -> None:
        """Initialize an error from Shopify subscription user-error messages.

        :param operation: Subscription operation rejected by Shopify.
        :param user_errors: Structured user errors returned by Shopify.
        """
        self.operation = operation
        self.user_errors = list(user_errors)
        self.messages = [error.message for error in self.user_errors]
        details = "; ".join(self.messages) if self.messages else "Unknown Shopify error"
        super().__init__(f"Webhook subscription {operation} failed: {details}")
