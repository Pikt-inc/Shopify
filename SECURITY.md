# Security Policy

## Reporting a vulnerability

Please report security issues privately by opening a GitHub security advisory or by contacting the repository owner directly. Do not open a public issue for vulnerabilities, exposed credentials, or store-specific data.

Include enough detail to reproduce or understand the issue:

- affected package version or commit
- affected module or API surface
- expected impact
- safe reproduction steps, if available

## Credential handling

This SDK is designed to receive Shopify credentials from environment variables or caller-managed configuration. Do not commit real store domains, Admin API access tokens, customer data, order data, or product IDs tied to a private store.

Use placeholder values in documentation and examples, such as:

```bash
SHOPIFY_SHOP_DOMAIN=example.myshopify.com
SHOPIFY_ACCESS_TOKEN=replace-with-shopify-admin-access-token
```

If a real Shopify token is committed, revoke or rotate it in Shopify immediately before cleaning up repository references.
