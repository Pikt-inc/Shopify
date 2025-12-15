from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional

from shopify_sdk import client
from shopify_sdk.gql import orders as OrdersQuery
from shopify_sdk.gql.core.types import Order, OrderConnection, OrderSortKeys, LineItem, ProductVariant, ShippingLine, Fulfillment


def _build_processed_at_query(days: int) -> str:
    """Return a Shopify order search query for orders processed within the last `days` days."""
    if days < 1:
        raise ValueError("days must be at least 1.")
    since = datetime.now(timezone.utc) - timedelta(days=days)
    timestamp = since.strftime("%Y-%m-%dT%H:%M:%SZ")
    return f'processed_at:>="{timestamp}"'


def iter_orders_from_last_n_days(
    days: int,
    page_size: int = 100,
    *,
    sort_key: OrderSortKeys = OrderSortKeys.PROCESSED_AT,
    reverse: bool = True,
) -> Iterable[Order]:
    """
    Yield orders processed within the last `days` days, following pagination cursors until complete.
    """
    if page_size < 1:
        raise ValueError("page_size must be at least 1.")

    query_string = _build_processed_at_query(days)
    cursor: Optional[str] = None

    while True:
        page: OrderConnection = OrdersQuery(
            first=page_size,
            after=cursor,
            sortKey=sort_key,
            reverse=reverse,
            query=query_string,
            field_exclusions={
                "OrderConnection": {"edges"},
                "LineItemConnection": {"edges"},
                "Order": set(Order.fields_except(
                    exclude={
                        "id", "shippingLines", "lineItems", "fulfillments", "legacyResourceId",
                        "name", "tags", "note", "sourceName", "presentmentCurrencyCode", "currencyCode",
                        "processedAt", "createdAt", "updatedAt", "cancelledAt", "cancelReason", "confirmed",
                        "displayFinancialStatus", "displayFulfillmentStatus", "subtotalPriceSet",
                        "totalPriceSet", "totalShippingPriceSet", "totalTaxSet", "totalDiscountsSet",
                        "transactions", "refunds"
                    }
                )),
                "LineItem": set(LineItem.fields_except(
                    exclude={
                        "id", "sku", "name", "title", "quantity",
                        "fulfillableQuantity", "fulfillmentStatus", "variantTitle",
                        "customAttributes", "discountedTotalSet", "originalUnitPriceSet",
                        "discountedUnitPriceSet", "variant", "taxLines"
                    }
                )),
                "ProductVariant": set(ProductVariant.fields_except(
                    exclude={"id", "sku"}
                )),
                "Fulfillment": set(Fulfillment.fields_except(
                    exclude={"id", "trackingInfo", "fulfillmentLineItems"}
                )),
                "ShippingLine": set(ShippingLine.fields_except(
                    exclude={"title", "code", "originalPriceSet"}
                )),
            },
        ).execute(client=client)

        for order in page.nodes or []:
            yield order

        page_info = page.pageInfo
        if not page_info or not page_info.hasNextPage or not page_info.endCursor:
            break
        cursor = page_info.endCursor


def get_orders_from_last_n_days(
    days: int,
    page_size: int = 100,
    *,
    sort_key: OrderSortKeys = OrderSortKeys.PROCESSED_AT,
    reverse: bool = True,
) -> list[Order]:
    """
    Convenience wrapper that returns a list of orders from the last `days` days.
    """
    return list(
        iter_orders_from_last_n_days(
            days=days,
            page_size=page_size,
            sort_key=sort_key,
            reverse=reverse
        )
    )
