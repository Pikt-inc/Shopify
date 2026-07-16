# Changelog

All notable changes to this package are documented here.

## 0.3.11

- Added typed Shopify `2026-07` metafield-definition creation for explicit deployment bootstrap operations.
- Preserved structured definition-create user errors and retained the SDK's no-retry mutation behavior.
- Removed import-time dotenv and credential loading; legacy unscoped environment credentials now resolve lazily.
- Restored package import compatibility with supported Python 3.10 runtimes.

## 0.3.10

- Added typed Shopify `2026-07` product custom-ID lookup and `productSet` upsert identifiers.
- Added read-only product custom-ID metafield definition inspection.
- Changed `ProductSetInput` serialization to omit unspecified list fields while preserving explicit empty lists.

## 0.3.9

- Added typed `inventorySetQuantities` support for `2025-10` and `2026-07`.
- Added typed nested field arguments, including required inventory quantity state names.
- Added SDK-generated per-mutation idempotency keys for `2026-07` inventory quantity writes.

## 0.3.8

- Added bounded retries for safe bulk result-file downloads.
- Redacted signed URLs and result contents from bulk download, parse, terminal, and upload failure messages.

## 0.3.7

- Added typed bulk submission errors for query, mutation, and staged-upload user errors.
- Preserved Shopify error codes, field paths, and messages without retaining raw payloads.

## 0.3.6

- Added bounded retries for idempotent GraphQL query execution.
- Added Shopify `Retry-After` and GraphQL throttle-cost recovery handling.
- Kept mutations and direct client requests single-attempt by default.

## 0.3.5

- Added opt-in flat bulk-query records for Shopify `groupObjects: false` output.
- Preserved typed parent provenance and resumable checkpoints for flat JSONL records.

## 0.3.4

- Added typed bulk-operation terminal metadata and resumable JSONL result checkpoints.
- Preserved bulk result `__lineNumber` and `__parentId` provenance in typed payloads.
- Added terminal failure details for Shopify error codes and partial-result URLs.

## 0.3.3

- Added safe cursor pagination for top-level locations and publications.
- Added cursor safety checks for missing, repeated, and empty continuation pages.
- Corrected nullable terminal cursors in the `2025-10` `PageInfo` contract.

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
