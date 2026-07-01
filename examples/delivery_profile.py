"""Attach variants to a named Shopify delivery profile."""

from __future__ import annotations

import os

from shopify_sdk import store


def main() -> None:
    """Find or create a delivery profile and attach configured variants."""

    variant_ids = [os.environ["SHOPIFY_VARIANT_ID"]]
    with store.credentials_context(
        shop_domain=os.environ["SHOPIFY_SHOP_DOMAIN"],
        access_token=os.environ["SHOPIFY_ACCESS_TOKEN"],
        api_version=os.getenv("SHOPIFY_API_VERSION", "2025-10"),
    ):
        profile_id = store.delivery.upsert_profile(
            name="Calculated Shipping",
            variant_ids=variant_ids,
        )

    print(profile_id)


if __name__ == "__main__":
    main()
