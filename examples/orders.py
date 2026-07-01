"""Query recent paid Shopify orders."""

from __future__ import annotations

import os

from shopify_sdk import store
from shopify_sdk.gql.core.types import OrderDisplayFinancialStatus


def main() -> None:
    """Print orders paid in the last 30 days."""

    with store.credentials_context(
        shop_domain=os.environ["SHOPIFY_SHOP_DOMAIN"],
        access_token=os.environ["SHOPIFY_ACCESS_TOKEN"],
        api_version=os.getenv("SHOPIFY_API_VERSION", "2025-10"),
    ):
        orders = store.orders.query(
            financial_status=OrderDisplayFinancialStatus.PAID,
            time=store.orders.Time.LAST_30_DAYS,
        )

    for order in orders.nodes:
        print(order.id, order.createdAt, order.financialStatus)


if __name__ == "__main__":
    main()
