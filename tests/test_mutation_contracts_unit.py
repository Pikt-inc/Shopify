from __future__ import annotations

from importlib import import_module
from typing import cast

import pytest

from shopify_sdk.gql.core.client import GQLResponse
from shopify_sdk.gql.core.client import RequestRetryMode
from shopify_sdk.gql.core.client import ShopifyClient


class FakeClient:
    def __init__(self, mutation_name: str, payload: dict[str, object]) -> None:
        self._mutation_name = mutation_name
        self._payload = payload

    def request(
        self,
        query: str,
        variables: dict[str, object],
        *,
        retry_mode: RequestRetryMode = RequestRetryMode.NEVER,
    ) -> GQLResponse:
        return GQLResponse(data={self._mutation_name: self._payload})


def _modules(version: str):
    package = f"shopify_sdk.gql.versions.{version}"
    return (
        import_module(f"{package}.mutations"),
        import_module(f"{package}.types.input_objects"),
        import_module(f"{package}.types.payload"),
    )


def _mutations(input_objects):
    return {
        "productUnpublish": (
            {
                "input": input_objects.ProductUnpublishInput(
                    id="gid://shopify/Product/1",
                    productPublications=[
                        input_objects.ProductPublicationInput(
                            publicationId="gid://shopify/Publication/1"
                        )
                    ],
                )
            },
            {"product": None, "shop": None, "userErrors": []},
        ),
        "productVariantsBulkCreate": (
            {
                "productId": "gid://shopify/Product/1",
                "variants": [input_objects.ProductVariantsBulkInput(price="9.99")],
            },
            {"product": None, "productVariants": [], "userErrors": []},
        ),
        "orderUpdate": (
            {
                "input": input_objects.OrderInput(
                    id="gid://shopify/Order/1",
                    note="updated",
                )
            },
            {"order": None, "userErrors": []},
        ),
        "fulfillmentCreateV2": (
            {
                "fulfillment": input_objects.FulfillmentV2Input(
                    lineItemsByFulfillmentOrder=[
                        input_objects.FulfillmentOrderLineItemsInput(
                            fulfillmentOrderId="gid://shopify/FulfillmentOrder/1",
                            fulfillmentOrderLineItems=[],
                        )
                    ]
                )
            },
            {"fulfillment": None, "userErrors": []},
        ),
    }


@pytest.mark.parametrize("version", ["v2025_10", "v2026_07"])
def test_mutations_with_missing_return_types_execute_as_typed_payloads(
    version: str,
) -> None:
    mutations, input_objects, payloads = _modules(version)
    expected_payload_names = {
        "productUnpublish": "ProductUnpublishPayload",
        "productVariantsBulkCreate": "ProductVariantsBulkCreatePayload",
        "orderUpdate": "OrderUpdatePayload",
        "fulfillmentCreateV2": "FulfillmentCreateV2Payload",
    }

    for mutation_name, (arguments, response_payload) in _mutations(input_objects).items():
        mutation_class = getattr(mutations, mutation_name)
        payload_name = expected_payload_names[mutation_name]
        mutation = mutation_class(
            **arguments,
            field_inclusions={payload_name: {"userErrors"}},
        )
        result = mutation.execute(
            cast(ShopifyClient, FakeClient(mutation_name, response_payload))
        )

        assert mutation.return_type is getattr(payloads, payload_name)
        assert result.userErrors == []


@pytest.mark.parametrize("version", ["v2025_10", "v2026_07"])
def test_variant_bulk_create_preserves_structured_user_errors(version: str) -> None:
    mutations, input_objects, _ = _modules(version)
    mutation = mutations.productVariantsBulkCreate(
        productId="gid://shopify/Product/1",
        variants=[input_objects.ProductVariantsBulkInput(price="9.99")],
        field_inclusions={"ProductVariantsBulkCreatePayload": {"userErrors"}},
    )
    result = mutation.execute(
        cast(
            ShopifyClient,
            FakeClient(
                "productVariantsBulkCreate",
                {
                    "product": None,
                    "productVariants": [],
                    "userErrors": [
                        {
                            "code": "INVALID_INPUT",
                            "field": ["variants", "0", "price"],
                            "message": "Price is invalid.",
                        }
                    ],
                },
            ),
        )
    )

    error = result.userErrors[0]
    assert error.code == "INVALID_INPUT"
    assert error.field == ["variants", "0", "price"]
    assert error.message == "Price is invalid."
