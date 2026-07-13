from shopify_sdk.gql.versions.v2026_07.mutations import webhookSubscriptionCreate
from shopify_sdk.gql.versions.v2026_07.queries import webhookSubscriptions
from shopify_sdk.gql.versions.v2026_07.types.enums import WebhookSubscriptionTopic
from shopify_sdk.gql.versions.v2026_07.types.input_objects import (
    WebhookSubscriptionInput,
)
from shopify_sdk.gql.core.client import ShopifyClient
from typing import cast


class FakeGraphQLClient:
    def request(self, query: str, variables: dict[str, object]):
        return type(
            "Response",
            (),
            {
                "data": {
                    "webhookSubscriptions": {
                        "edges": [],
                        "nodes": [
                            {
                                "id": "gid://shopify/WebhookSubscription/1",
                                "topic": "ORDERS_CREATE",
                                "uri": "https://example.test/webhooks/orders",
                                "includeFields": ["id"],
                                "metafieldNamespaces": [],
                            }
                        ],
                        "pageInfo": {
                            "hasNextPage": False,
                            "hasPreviousPage": False,
                            "startCursor": None,
                            "endCursor": None,
                        },
                    }
                }
            },
        )()


def test_create_mutation_uses_webhook_topic_graphql_enum_type() -> None:
    mutation = webhookSubscriptionCreate(
        topic=WebhookSubscriptionTopic("ORDERS_CREATE"),
        webhookSubscription=WebhookSubscriptionInput(
            uri="https://example.test/webhooks/orders"
        ),
    )

    assert "$topic: WebhookSubscriptionTopic!" in mutation.body
    assert mutation.variables["topic"] == "ORDERS_CREATE"
    assert mutation.variables["webhookSubscription"] == {
        "uri": "https://example.test/webhooks/orders"
    }


def test_subscription_list_query_uses_versioned_topic_type() -> None:
    query = webhookSubscriptions(
        first=10,
        topics=[WebhookSubscriptionTopic("APP_UNINSTALLED")],
    )

    assert "$topics: [WebhookSubscriptionTopic!]" in query.body
    assert query.variables["topics"] == ["APP_UNINSTALLED"]


def test_subscription_list_query_parses_typed_connection_response() -> None:
    query = webhookSubscriptions(first=1)

    response = query.execute(cast(ShopifyClient, FakeGraphQLClient()))

    assert response.nodes[0].id == "gid://shopify/WebhookSubscription/1"
    assert response.nodes[0].topic == "ORDERS_CREATE"
    assert response.nodes[0].includeFields == ["id"]
