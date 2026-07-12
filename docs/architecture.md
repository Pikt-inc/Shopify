# Architecture

`shopify_sdk` is a typed wrapper around the Shopify Admin GraphQL API. The package keeps Shopify's GraphQL shape visible while reducing repetitive boilerplate around credentials, field selection, typed payload construction, pagination, bulk operations, and common ecommerce workflows.

## Design goals

- Keep GraphQL operations explicit and debuggable.
- Represent inputs and responses with typed Python models.
- Provide manager APIs for common production workflows.
- Support high-volume sync jobs through bulk helpers.
- Keep credential scope local to the operation being run.
- Make API errors and Shopify user errors visible to callers.

## Layer 1: GraphQL core

The GraphQL core owns the low-level request lifecycle:

- API client and credential context
- query and mutation objects
- field-selection controls
- execution helpers
- bulk query and bulk mutation support
- typed response parsing

The key entry points are exposed through `shopify_sdk.gql` and `shopify_sdk.gql.core`.

Example:

```python
from shopify_sdk.gql import client_context, products

with client_context(
    shop_domain="example.myshopify.com",
    access_token="<SHOPIFY_ADMIN_ACCESS_TOKEN>",
    api_version="2026-07",
):
    query = products(query="status:active")
    connection = query.bulk()
```

## Layer 2: Typed schema objects

The SDK models Shopify GraphQL inputs and responses with Pydantic-backed types:

- input objects, such as `ProductSetInput` and `DeliveryProfileInput`
- enums, such as `ProductStatus` and `OrderDisplayFinancialStatus`
- object models, such as `Product`, `Order`, and `ProductVariant`
- connections, edges, and mutation payloads

This makes call sites easier to validate and review than raw dictionaries or ad hoc GraphQL strings.

Version-specific schema import paths live under
`shopify_sdk.gql.versions.<version>.types`. The compatibility imports under
`shopify_sdk.gql.core.types` point at the latest default version, while
manager/query/mutation entry points resolve the active version from the current
client context.

Example:

```python
from shopify_sdk.gql.core.types import ProductSetInput

payload = ProductSetInput(
    handle="example-product",
    title="Example Product",
    tags=["example", "sdk"],
)
```

## Layer 3: Managers

Managers wrap common Shopify workflows that appear repeatedly in catalog, inventory, order, media, and delivery automation.

The top-level `store` manager exposes:

- `store.products`
- `store.products.bulk`
- `store.products.variants`
- `store.orders`
- `store.delivery`
- `store.map`

Manager methods keep workflow code shorter while still returning typed SDK objects.

Example:

```python
from shopify_sdk import store

with store.credentials_context("example.myshopify.com", "<SHOPIFY_ADMIN_ACCESS_TOKEN>"):
    handle_to_id = store.products.bulk.get_handle_id_map(query="status:active")
```

## Bulk operations

Shopify bulk operations are useful for high-volume stores, but they introduce extra bookkeeping: operation creation, polling, result parsing, and connection reconstruction.

The SDK wraps those details in manager helpers such as:

- `store.products.query_all(...)`
- `store.products.bulk.get_handle_id_map(...)`
- `store.products.bulk.partition_handles_by_tag(...)`
- `store.products.variants.query_all(...)`
- `store.products.bulk.set(...)`

These helpers are designed for synchronization flows that need to compare external inventory against Shopify's current product and variant state.

## Delivery profiles

The delivery manager focuses on profile assignment and reconciliation:

- assign flat-rate shipping profiles
- find or create named delivery profiles
- attach variants idempotently
- leave merchant-owned rates untouched when appropriate

This keeps shipping orchestration code separate from product publishing code.

## Error handling

The SDK surfaces failures in two categories:

1. transport or GraphQL request failures raised by the client layer
2. Shopify mutation `userErrors` detected by manager methods

Manager methods generally raise `ValueError` when a mutation reports user errors that prevent the requested operation from succeeding. Callers can catch those errors at orchestration boundaries and decide whether to retry, skip, or alert.

## Testing strategy

The test suite focuses on unit-level behavior around manager methods, typed payloads, query construction, and mutation orchestration. The pull request workflow runs:

- `mypy .`
- `ruff check .`
- `ruff format --check .`
- `python -m pytest`
- `vulture ./shopify_sdk/ --min-confidence 100`

This keeps the SDK suitable for production automation while remaining small enough to inspect and evolve quickly.
