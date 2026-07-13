from types import SimpleNamespace
from typing import cast

import pytest

from shopify_sdk.gql.core.client import client_context
from shopify_sdk.managers.webhooks import WebhookManager
from shopify_sdk.webhooks import UnsupportedWebhookApiVersion
from shopify_sdk.webhooks import WebhookSubscriptionCreateRequest
from shopify_sdk.webhooks import WebhookSubscriptionError
from shopify_sdk.webhooks import WebhookSubscriptionListRequest
from shopify_sdk.webhooks import WebhookSubscriptionUpdateRequest
from shopify_sdk.gql.versions.v2026_07.types.input_objects import (
    WebhookSubscriptionInput,
)


def _subscription(
    subscription_id: str = "gid://shopify/WebhookSubscription/1",
    topic: str = "ORDERS_CREATE",
    uri: str = "https://example.test/webhooks/orders",
) -> SimpleNamespace:
    return SimpleNamespace(id=subscription_id, topic=topic, uri=uri)


def _context(api_version: str):
    return client_context("example.myshopify.com", "token", api_version)


def test_list_uses_2026_query_with_filters(monkeypatch) -> None:
    from shopify_sdk.gql.versions.v2026_07 import queries

    captured: dict[str, object] = {}

    class FakeQuery:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

        def execute(self, _client: object) -> SimpleNamespace:
            return SimpleNamespace(nodes=[_subscription()])

    monkeypatch.setattr(queries, "webhookSubscriptions", FakeQuery)
    request = WebhookSubscriptionListRequest(
        first=10,
        after="cursor-1",
        topics=["ORDERS_CREATE"],
        uri="https://example.test/webhooks/orders",
    )

    with _context("2026-07"):
        result = WebhookManager().list(request)

    assert result.nodes[0].topic == "ORDERS_CREATE"
    assert captured["first"] == 10
    assert captured["after"] == "cursor-1"
    assert captured["topics"] == ["ORDERS_CREATE"]
    assert captured["uri"] == "https://example.test/webhooks/orders"


def test_create_maps_request_to_versioned_mutation(monkeypatch) -> None:
    from shopify_sdk.gql.versions.v2026_07 import mutations

    captured: dict[str, object] = {}

    class FakeMutation:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

        def execute(self, _client: object) -> SimpleNamespace:
            return SimpleNamespace(userErrors=[], webhookSubscription=_subscription())

    monkeypatch.setattr(mutations, "webhookSubscriptionCreate", FakeMutation)
    request = WebhookSubscriptionCreateRequest(
        topic="ORDERS_CREATE",
        uri="https://example.test/webhooks/orders",
        filter="financial_status:paid",
        include_fields=["id", "note"],
        metafield_namespaces=["custom"],
        name="orders-paid",
    )

    with _context("2026-07"):
        result = WebhookManager().create(request)

    assert result.id == "gid://shopify/WebhookSubscription/1"
    assert captured["topic"] == "ORDERS_CREATE"
    input_data = cast(WebhookSubscriptionInput, captured["webhookSubscription"])
    assert input_data.to_graphql() == {
        "uri": "https://example.test/webhooks/orders",
        "filter": "financial_status:paid",
        "includeFields": ["id", "note"],
        "metafieldNamespaces": ["custom"],
        "name": "orders-paid",
    }


def test_update_maps_only_explicit_request_fields(monkeypatch) -> None:
    from shopify_sdk.gql.versions.v2026_07 import mutations

    captured: dict[str, object] = {}

    class FakeMutation:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

        def execute(self, _client: object) -> SimpleNamespace:
            return SimpleNamespace(userErrors=[], webhookSubscription=_subscription())

    monkeypatch.setattr(mutations, "webhookSubscriptionUpdate", FakeMutation)
    request = WebhookSubscriptionUpdateRequest(
        id="gid://shopify/WebhookSubscription/1",
        include_fields=["id", "updated_at"],
    )

    with _context("2026-07"):
        WebhookManager().update(request)

    assert captured["id"] == "gid://shopify/WebhookSubscription/1"
    input_data = cast(WebhookSubscriptionInput, captured["webhookSubscription"])
    assert input_data.to_graphql() == {
        "includeFields": ["id", "updated_at"]
    }


def test_delete_returns_deleted_subscription_id(monkeypatch) -> None:
    from shopify_sdk.gql.versions.v2026_07 import mutations

    class FakeMutation:
        def __init__(self, **kwargs: object) -> None:
            self._id = kwargs["id"]

        def execute(self, _client: object) -> SimpleNamespace:
            return SimpleNamespace(
                userErrors=[],
                deletedWebhookSubscriptionId=self._id,
            )

    monkeypatch.setattr(mutations, "webhookSubscriptionDelete", FakeMutation)

    with _context("2026-07"):
        deleted_id = WebhookManager().delete("gid://shopify/WebhookSubscription/1")

    assert deleted_id == "gid://shopify/WebhookSubscription/1"


def test_manager_rejects_unsupported_api_version() -> None:
    with _context("2025-10"):
        with pytest.raises(UnsupportedWebhookApiVersion, match="2026-07"):
            WebhookManager().list()


def test_manager_raises_structured_error_for_user_errors(monkeypatch) -> None:
    from shopify_sdk.gql.versions.v2026_07 import mutations

    class FakeMutation:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def execute(self, _client: object) -> SimpleNamespace:
            return SimpleNamespace(
                userErrors=[
                    SimpleNamespace(
                        field=["webhookSubscription", "uri"],
                        message="URI is invalid",
                    )
                ],
                webhookSubscription=None,
            )

    monkeypatch.setattr(mutations, "webhookSubscriptionCreate", FakeMutation)
    request = WebhookSubscriptionCreateRequest(
        topic="ORDERS_CREATE",
        uri="https://example.test/webhooks/orders",
    )

    with _context("2026-07"):
        with pytest.raises(WebhookSubscriptionError, match="URI is invalid") as exc_info:
            WebhookManager().create(request)

    assert exc_info.value.user_errors[0].field == ["webhookSubscription", "uri"]


def test_update_request_requires_a_changed_field() -> None:
    with pytest.raises(ValueError, match="at least one changed field"):
        WebhookSubscriptionUpdateRequest(id="gid://shopify/WebhookSubscription/1")


def test_update_request_rejects_explicit_null_uri() -> None:
    with pytest.raises(ValueError, match="URI cannot be cleared"):
        WebhookSubscriptionUpdateRequest(
            id="gid://shopify/WebhookSubscription/1",
            uri=None,
        )


def test_find_uses_next_page_when_first_page_has_no_match(monkeypatch) -> None:
    from shopify_sdk.gql.versions.v2026_07 import queries

    requested_cursors: list[object] = []

    class FakeQuery:
        def __init__(self, **kwargs: object) -> None:
            requested_cursors.append(kwargs["after"])

        def execute(self, _client: object) -> SimpleNamespace:
            if len(requested_cursors) == 1:
                return SimpleNamespace(
                    nodes=[],
                    pageInfo=SimpleNamespace(hasNextPage=True, endCursor="cursor-2"),
                )
            return SimpleNamespace(
                nodes=[_subscription()],
                pageInfo=SimpleNamespace(hasNextPage=False, endCursor=None),
            )

    monkeypatch.setattr(queries, "webhookSubscriptions", FakeQuery)

    with _context("2026-07"):
        result = WebhookManager().find(
            "ORDERS_CREATE",
            "https://example.test/webhooks/orders",
        )

    assert result is not None
    assert requested_cursors == [None, "cursor-2"]
