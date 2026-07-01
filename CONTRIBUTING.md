# Contributing

Thanks for improving `shopify_sdk`. This repository is intentionally small and typed, so contributions should keep Shopify GraphQL behavior explicit while reducing repetitive application code.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Local checks

Run the same checks used by CI before opening a pull request:

```bash
mypy .
ruff check .
ruff format --check .
python -m pytest
vulture ./shopify_sdk/ --min-confidence 100
```

For documentation-only or example-only changes, at minimum run `ruff` and `python -m py_compile` against the touched Python files.

## Code guidelines

- Keep manager APIs focused on production Shopify workflows.
- Prefer typed input and response objects over raw dictionaries.
- Keep GraphQL fields explicit so API calls remain debuggable.
- Surface Shopify `userErrors` clearly at manager boundaries.
- Avoid embedding real store domains, access tokens, product IDs, or customer data in examples or tests.

## Pull request checklist

- [ ] Added or updated tests for behavior changes.
- [ ] Updated examples or docs when public usage changes.
- [ ] Ran relevant local checks.
- [ ] Confirmed no credentials or private store data are committed.
