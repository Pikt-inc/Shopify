from shopify_sdk.common import set_order_line_item_tracking
set_order_line_item_tracking(
    order_id="gid://shopify/Order/6756039033083",
    line_item_id="gid://shopify/LineItem/16550326337787",
    tracking_number="1234567890",
    carrier="UPS",
    quantity=1
)