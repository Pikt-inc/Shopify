from shopify_sdk.gql import orders
from shopify_sdk.gql.core.types import OrderSortKeys
from shopify_sdk import client


def format_order(order) -> str:
    """Build a concise string for an order node."""
    return (
        f"id={order.id} "
        f"processedAt={order.processedAt} "
        f"financial={order.displayFinancialStatus} "
        f"fulfillment={order.displayFulfillmentStatus} "
        f"lineItems={order.lineItems.count}"
    )


def main():
    latest = orders(
        first=3,
        sortKey=OrderSortKeys.PROCESSED_AT,
        reverse=True,
    ).execute(client=client)

    print("\n=== Latest Orders ===")
    if not latest.nodes:
        print("No orders returned.")
        return

    for order in latest.nodes:
        print(format_order(order))

    # Example: inspect first line items of the newest order
    newest = latest.first
    if newest and newest.lineItems.nodes:
        print("\nFirst line items of newest order:")
        for item in newest.lineItems.nodes:
            print(f"- {item.title} x{item.quantity}")


if __name__ == "__main__":
    main()

