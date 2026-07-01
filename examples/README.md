# Examples

These examples demonstrate the intended public-facing SDK usage patterns. They use environment variables and placeholder IDs so they can be copied into a local script without embedding private store data.

Required environment variables for examples that call Shopify:

```bash
export SHOPIFY_SHOP_DOMAIN="example.myshopify.com"
export SHOPIFY_ACCESS_TOKEN="replace-with-shopify-admin-access-token"
export SHOPIFY_API_VERSION="2025-10"
```

Copy [`.env.example`](../.env.example) if you want a local starting point for environment variables.

Examples:

- [`query_products.py`](query_products.py) - query active products through the manager API.
- [`product_set.py`](product_set.py) - build typed `ProductSetInput` payloads and submit them with `productSet`.
- [`metafields.py`](metafields.py) - attach product-level metafields to a typed `ProductSetInput` payload.
- [`orders.py`](orders.py) - query recent paid orders.
- [`delivery_profile.py`](delivery_profile.py) - attach variants to a named delivery profile.

All examples are intentionally short and focused. Production integrations should add application-specific logging, retries, and error handling around these primitives.
