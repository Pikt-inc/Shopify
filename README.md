# Shopify SDK

[![Package verification](https://github.com/Pikt-inc/Shopify/actions/workflows/package.yml/badge.svg)](https://github.com/Pikt-inc/Shopify/actions/workflows/package.yml)

Typed Python SDK for the Shopify Admin GraphQL API.

This package wraps Shopify GraphQL queries, mutations, typed input objects, and common ecommerce workflows behind a Python interface. It is designed for production sync jobs where raw GraphQL strings, response parsing, and bulk-operation bookkeeping become repetitive and error-prone.

## Highlights

- Typed GraphQL input and response models built with Pydantic.
- Query and mutation builders with explicit field-selection support.
- Credential context management for safe per-store API calls.
- Manager APIs for products, variants, orders, media, delivery profiles, inventory, and handle mapping.
- Bulk helpers for high-volume product and variant workflows.
- Unit tests and CI checks for manager behavior, typed payloads, formatting, and static analysis.

## Why this exists

Shopify Admin GraphQL is powerful, but production integrations often repeat the same concerns:

- hand-written query and mutation strings
- inconsistent field selections
- typed payload construction
- paginated and bulk operation handling
- user-error extraction after mutations
- store-scoped credential management

`shopify_sdk` keeps the GraphQL API visible while providing typed Python primitives and manager-level operations for the workflows that come up repeatedly in catalog, fulfillment, and delivery automation.

## Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/Pikt-inc/Shopify.git
```

For local development:

```bash
git clone https://github.com/Pikt-inc/Shopify.git
cd Shopify
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Quick start

```python
import os

from shopify_sdk import store


with store.credentials_context(
    shop_domain=os.environ["SHOPIFY_SHOP_DOMAIN"],
    access_token=os.environ["SHOPIFY_ACCESS_TOKEN"],
    api_version=os.getenv("SHOPIFY_API_VERSION", "2026-07"),
):
    products = store.products.query_all(query="status:active")

for product in products.nodes:
    print(product.id, product.handle, product.title)
```

## API versions

The SDK defaults to Shopify Admin GraphQL API version `2026-07`. Set
`SHOPIFY_API_VERSION` or pass `api_version` to `credentials_context` to use a
different supported schema version. The currently versioned GraphQL
implementations are `2025-10` and `2026-07`.

## Manager examples

Query active products:

```python
from shopify_sdk import store

products = store.products.query_all(query="status:active")
```

Create or update products with `productSet`:

```python
from shopify_sdk import store
from shopify_sdk.gql.core.types import ProductSetInput

payload = ProductSetInput(
    handle="example-product",
    title="Example Product",
    descriptionHtml="<p>Created through shopify_sdk.</p>",
    tags=["example", "sdk"],
)

responses = store.products.bulk.set([payload])
```

Read named inventory quantity states:

```python
from shopify_sdk import client
from shopify_sdk.gql.queries import locations

inventory_query = locations(
    field_inclusions={
        "Location": {"id", "inventoryLevels"},
        "InventoryLevel": {"id", "quantities"},
        "InventoryQuantity": {"name", "quantity"},
    },
).with_field_arguments(
    {
        "InventoryLevel": {
            "quantities": {"names": ["available", "on_hand"]},
        }
    }
)

location_connection = inventory_query.execute(client)
```

Set an absolute inventory quantity when the application is the source of truth:

```python
from shopify_sdk import client
from shopify_sdk.gql.core.types import (
    InventoryQuantityInput,
    InventorySetQuantitiesInput,
)
from shopify_sdk.gql.mutations import inventorySetQuantities

payload = inventorySetQuantities(
    input=InventorySetQuantitiesInput(
        name="available",
        reason="correction",
        quantities=[
            InventoryQuantityInput(
                inventoryItemId="gid://shopify/InventoryItem/1",
                locationId="gid://shopify/Location/1",
                quantity=42,
                changeFromQuantity=None,
            )
        ],
    )
).execute(client)
```

On `2026-07`, the SDK generates the required idempotency key automatically. Pass
`idempotency_key=` to `inventorySetQuantities` to provide a stable application key.

Stream flat bulk-query records after persisting a checkpoint:

```python
from shopify_sdk.gql.core.bulk import bulk_query_handle
from shopify_sdk.gql.queries import products

handle = bulk_query_handle(products(first=50), group_objects=False)
for event in handle.iter_flat_results():
    process(event.record.data, parent_id=event.record.parent_id)
    save_checkpoint(event.checkpoint.model_dump())
```

Use a persisted `BulkOperationCheckpoint` with `handle.iter_flat_results(checkpoint)`
to reattach without resubmitting the Shopify bulk operation. A non-completed operation
raises `BulkOperationTerminalError`, whose `state` preserves `error_code` and
`partial_data_url` when Shopify provides them. `group_objects` defaults to `True`; use
flat mode only when callers need Shopify's explicit parent-child JSONL relationships.

Handle rejected bulk submissions with stable error details:

```python
from shopify_sdk.gql.core.bulk import BulkOperationSubmissionError, bulk_query_handle

try:
    handle = bulk_query_handle(products(first=50), group_objects=False)
except BulkOperationSubmissionError as error:
    for user_error in error.errors:
        print(error.stage, user_error.code, user_error.field, user_error.message)
```

Bulk result-file downloads retry temporary network and `429`/`5xx` failures safely.
Exceptions and logs retain operation, status, and line metadata but redact signed URLs and
result contents. Bulk submissions and staged-upload POSTs remain single-attempt.

### Retry behavior

SDK query execution retries temporary Shopify failures by default; mutations and direct
`client.request()` calls remain single-attempt to avoid duplicate writes. The starting
policy uses three total attempts, a one-second exponential-backoff delay, an eight-second
maximum delay, and 20% jitter. A valid numeric Shopify `Retry-After` value takes priority.

Pass a policy through `credentials_context` to change this behavior for a shop context:

```python
from shopify_sdk import store
from shopify_sdk.gql.core.client import ShopifyRetryPolicy

policy = ShopifyRetryPolicy(max_attempts=1)
with store.credentials_context(
    shop_domain="example.myshopify.com",
    access_token="token",
    retry_policy=policy,
):
    products = store.products.query_all()
```

Query recent paid orders:

```python
from shopify_sdk import store
from shopify_sdk.gql.core.types import OrderDisplayFinancialStatus

orders = store.orders.query(
    financial_status=OrderDisplayFinancialStatus.PAID,
    time=store.orders.Time.LAST_30_DAYS,
)
```

Assign variants to a delivery profile:

```python
from shopify_sdk import store

profile_id = store.delivery.upsert_profile(
    name="Calculated Shipping",
    variant_ids=["gid://shopify/ProductVariant/1234567890"],
)
```

More focused examples live in [`examples/`](examples/).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for local setup, check commands, and pull request expectations.

## Security

See [`SECURITY.md`](SECURITY.md) for vulnerability reporting and credential-handling guidance.

## Architecture

The SDK is organized into three main layers:

1. **GraphQL core** - clients, query/mutation builders, field selection, bulk execution, and typed payload parsing.
2. **Typed schema objects** - Pydantic input objects, enums, GraphQL object models, connections, and payloads.
3. **Managers** - product, variant, order, media, delivery, and store-level helpers for common operational workflows.

See [`docs/architecture.md`](docs/architecture.md) for a deeper walkthrough.

## Development

Install dependencies:

```bash
pip install -r requirements.txt
pip install -e .
```

Run checks locally:

```bash
mypy .
ruff check .
ruff format --check .
python -m pytest
vulture ./shopify_sdk/ --min-confidence 100
```

The GitHub workflow runs type checks, linting, formatting checks, tests, and dead-code checks on pull requests.

## Project status

This package is a production-oriented SDK used for Shopify Admin GraphQL automation. The public API is intentionally small, but the package is still evolving with the operational workflows it supports.
