from shopify_sdk.gql.core.types import ID, String, Int

def ensure_order_gid(
    order_id: String | Int | ID
) -> ID:
    string_order_id = str(order_id)
    if 'gid://' in string_order_id:
        return order_id
    return f"gid://shopify/Order/{string_order_id}"

def ensure_fulfillment_order_line_item_gid(
    line_item_id: String | Int | ID
) -> ID:
    string_line_item_id = str(line_item_id)
    if 'gid://' in string_line_item_id:
        return line_item_id
    return f"gid://shopify/FulfillmentOrderLineItem/{string_line_item_id}"

def ensure_fulfillment_gid(
    fulfillment_id: String | Int | ID
) -> ID:
    string_fulfillment_id = str(fulfillment_id)
    if 'gid://' in string_fulfillment_id:
        return fulfillment_id
    return f"gid://shopify/Fulfillment/{string_fulfillment_id}"

def ensure_line_item_gid(
    line_item_id: String | Int | ID
) -> ID:
    string_line_item_id = str(line_item_id)
    if 'gid://' in string_line_item_id:
        return line_item_id
    return f"gid://shopify/LineItem/{string_line_item_id}"