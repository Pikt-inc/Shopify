from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, List, cast

from pydantic import BaseModel

from shopify_sdk.gql.core.client import current_api_version
from shopify_sdk.webhooks.exceptions import UnsupportedWebhookApiVersion
from shopify_sdk.webhooks.exceptions import WebhookSubscriptionError
from shopify_sdk.webhooks.subscriptions import WebhookSubscriptionCreateRequest
from shopify_sdk.webhooks.subscriptions import WebhookSubscriptionListRequest
from shopify_sdk.webhooks.subscriptions import WebhookSubscriptionUpdateRequest
from shopify_sdk.webhooks.subscriptions import WebhookSubscriptionUserError

if TYPE_CHECKING:
    from shopify_sdk.gql.versions.v2026_07.types.connections import (
        WebhookSubscriptionConnection,
    )
    from shopify_sdk.gql.versions.v2026_07.types.enums import (
        WebhookSubscriptionTopic,
    )
    from shopify_sdk.gql.versions.v2026_07.types.input_objects import (
        WebhookSubscriptionInput,
    )
    from shopify_sdk.gql.versions.v2026_07.types.objects import WebhookSubscription


class WebhookManager(BaseModel):
    """Manage 2026-07 shop-scoped webhook subscriptions through Admin GraphQL."""

    SUPPORTED_API_VERSION: ClassVar[str] = "2026-07"

    def list(
        self,
        request: WebhookSubscriptionListRequest | None = None,
    ) -> "WebhookSubscriptionConnection":
        """List API-created webhook subscriptions for the active shop.

        :param request: Optional topic, URI, search, and pagination filters.
        :returns: Paginated shop-scoped API webhook subscriptions.
        :raises UnsupportedWebhookApiVersion: If active API version is not 2026-07.
        """
        self._require_supported_api_version()
        from shopify_sdk import client
        from shopify_sdk.gql.versions.v2026_07.queries import webhookSubscriptions

        resolved_request = request or WebhookSubscriptionListRequest()
        query = webhookSubscriptions(
            first=resolved_request.first,
            topics=self._topics(resolved_request.topics),
            uri=resolved_request.uri,
            query=resolved_request.query,
            reverse=resolved_request.reverse,
            after=resolved_request.after,
        )
        return query.execute(client)

    def find(self, topic: str, uri: str) -> "WebhookSubscription | None":
        """Return the first API-created subscription matching a topic and URI.

        :param topic: Shopify GraphQL webhook topic value.
        :param uri: Exact HTTPS delivery URI.
        :returns: Matching subscription, when one exists.
        """
        request = WebhookSubscriptionListRequest(first=100, topics=[topic], uri=uri)
        while True:
            connection = self.list(request)
            subscription = next(
                (
                    item
                    for item in connection.nodes
                    if item.topic == topic and item.uri == uri
                ),
                None,
            )
            if subscription is not None:
                return subscription
            page_info = connection.pageInfo
            if not page_info.hasNextPage or not page_info.endCursor:
                return None
            request = request.model_copy(update={"after": page_info.endCursor})

    def create(
        self,
        request: WebhookSubscriptionCreateRequest,
    ) -> "WebhookSubscription":
        """Create a 2026-07 HTTP webhook subscription.

        :param request: Subscription topic and delivery configuration.
        :returns: Created webhook subscription.
        :raises WebhookSubscriptionError: If Shopify returns user errors.
        """
        self._require_supported_api_version()
        from shopify_sdk import client
        from shopify_sdk.gql.versions.v2026_07.mutations import (
            webhookSubscriptionCreate,
        )

        payload = webhookSubscriptionCreate(
            topic=self._topic(request.topic),
            webhookSubscription=self._create_input(request),
        ).execute(client)
        self._raise_if_user_errors("create", payload)
        subscription = getattr(payload, "webhookSubscription", None)
        if subscription is None:
            raise WebhookSubscriptionError(
                "create",
                [WebhookSubscriptionUserError(message="No subscription was returned.")],
            )
        return cast("WebhookSubscription", subscription)

    def update(
        self,
        request: WebhookSubscriptionUpdateRequest,
    ) -> "WebhookSubscription":
        """Update a 2026-07 HTTP webhook subscription.

        :param request: Subscription ID and explicitly supplied changed fields.
        :returns: Updated webhook subscription.
        :raises WebhookSubscriptionError: If Shopify returns user errors.
        """
        self._require_supported_api_version()
        from shopify_sdk import client
        from shopify_sdk.gql.versions.v2026_07.mutations import (
            webhookSubscriptionUpdate,
        )

        payload = webhookSubscriptionUpdate(
            id=request.id,
            webhookSubscription=self._update_input(request),
        ).execute(client)
        self._raise_if_user_errors("update", payload)
        subscription = getattr(payload, "webhookSubscription", None)
        if subscription is None:
            raise WebhookSubscriptionError(
                "update",
                [WebhookSubscriptionUserError(message="No subscription was returned.")],
            )
        return cast("WebhookSubscription", subscription)

    def delete(self, subscription_id: str) -> str:
        """Delete a 2026-07 API-created webhook subscription.

        :param subscription_id: Shopify GraphQL webhook subscription ID.
        :returns: Deleted subscription ID.
        :raises WebhookSubscriptionError: If Shopify returns user errors.
        """
        self._require_supported_api_version()
        from shopify_sdk import client
        from shopify_sdk.gql.versions.v2026_07.mutations import (
            webhookSubscriptionDelete,
        )

        payload = webhookSubscriptionDelete(id=subscription_id).execute(client)
        self._raise_if_user_errors("delete", payload)
        deleted_id = getattr(payload, "deletedWebhookSubscriptionId", None)
        if not deleted_id:
            raise WebhookSubscriptionError(
                "delete",
                [
                    WebhookSubscriptionUserError(
                        message="No deleted subscription ID returned."
                    )
                ],
            )
        return str(deleted_id)

    def _require_supported_api_version(self) -> None:
        """Reject subscription management outside the implemented schema version."""
        active_version = current_api_version()
        if active_version != self.SUPPORTED_API_VERSION:
            raise UnsupportedWebhookApiVersion(
                "Webhook subscription management currently supports only "
                f"{self.SUPPORTED_API_VERSION}; active version is {active_version}."
            )

    def _topics(
        self, topics: List[str] | None
    ) -> List["WebhookSubscriptionTopic"] | None:
        """Convert public topic strings to 2026-07 GraphQL topic values."""
        if topics is None:
            return None
        return [self._topic(topic) for topic in topics]

    def _topic(self, topic: str) -> "WebhookSubscriptionTopic":
        """Return a 2026-07 GraphQL topic wrapper from a public topic string."""
        from shopify_sdk.gql.versions.v2026_07.types.enums import (
            WebhookSubscriptionTopic,
        )

        return WebhookSubscriptionTopic(topic)

    def _create_input(
        self, request: WebhookSubscriptionCreateRequest
    ) -> "WebhookSubscriptionInput":
        """Map a create request to a versioned GraphQL subscription input."""
        from shopify_sdk.gql.versions.v2026_07.types.input_objects import (
            WebhookSubscriptionInput,
        )

        input_data = WebhookSubscriptionInput(uri=request.uri)
        if request.filter is not None:
            input_data.filter = request.filter
        if request.include_fields:
            input_data.includeFields = request.include_fields
        if request.metafield_namespaces:
            input_data.metafieldNamespaces = request.metafield_namespaces
        if request.name is not None:
            input_data.name = request.name
        return input_data

    def _update_input(
        self, request: WebhookSubscriptionUpdateRequest
    ) -> "WebhookSubscriptionInput":
        """Map explicitly supplied update fields to a GraphQL subscription input."""
        from shopify_sdk.gql.versions.v2026_07.types.input_objects import (
            WebhookSubscriptionInput,
        )

        input_data = WebhookSubscriptionInput()
        request_to_input_fields = {
            "uri": "uri",
            "filter": "filter",
            "include_fields": "includeFields",
            "metafield_namespaces": "metafieldNamespaces",
            "name": "name",
        }
        for request_field, input_field in request_to_input_fields.items():
            if request_field in request.model_fields_set:
                setattr(input_data, input_field, getattr(request, request_field))
        return input_data

    def _raise_if_user_errors(self, operation: str, payload: object) -> None:
        """Raise a domain error when a Shopify payload contains user errors."""
        user_errors = getattr(payload, "userErrors", []) or []
        structured_errors = [
            WebhookSubscriptionUserError(
                field=getattr(error, "field", None),
                message=str(getattr(error, "message", error)),
            )
            for error in user_errors
        ]
        if structured_errors:
            raise WebhookSubscriptionError(operation, structured_errors)
