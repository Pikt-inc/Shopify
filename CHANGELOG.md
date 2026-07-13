# Changelog

All notable changes to this package are documented here.

## 0.3.2

- Added injectable Shopify HTTP transport and structured transport errors.
- Added deterministic offline transport tests and CI unit-test verification.
- Added typed payloads for existing product, order, and fulfillment mutations.

## 0.3.1

- Declared runtime dependencies in package metadata.
- Added a clean-install package verification script and GitHub Actions workflow.
- Added development extras for test, lint, type-check, and static-analysis tools.

## 0.1.88

- Added typed inventory adjustment payload support.
- Added delivery-profile helpers for named profile upserts and variant assignment.
- Preserved product tags on product update payloads.
- Expanded unit coverage for inventory, product update, delivery, and weight input behavior.
- Added README, architecture documentation, focused examples, package metadata, and MIT license documentation.

## 0.1.87

- Preserved existing Shopify product tags when product update inputs omit tag changes.

## 0.1.86

- Added a generic delivery profile upsert primitive for finding or creating named delivery profiles.
