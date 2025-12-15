from shopify_sdk.gql.core.types import ID, String, Int

def ensure_order_gid(
    order_id: String | Int | ID
) -> ID:
    if order_id is None:
        return None
    string_order_id = str(order_id)
    if 'gid://' in string_order_id:
        return string_order_id
    return f"gid://shopify/Order/{string_order_id}"

def ensure_fulfillment_order_line_item_gid(
    line_item_id: String | Int | ID
) -> ID:
    if line_item_id is None:
        return None
    string_line_item_id = str(line_item_id)
    if 'gid://' in string_line_item_id:
        return string_line_item_id
    return f"gid://shopify/FulfillmentOrderLineItem/{string_line_item_id}"

def ensure_fulfillment_gid(
    fulfillment_id: String | Int | ID
) -> ID:
    if fulfillment_id is None:
        return None
    string_fulfillment_id = str(fulfillment_id)
    if 'gid://' in string_fulfillment_id:
        return string_fulfillment_id
    return f"gid://shopify/Fulfillment/{string_fulfillment_id}"

def ensure_line_item_gid(
    line_item_id: String | Int | ID
) -> ID:
    if line_item_id is None:
        return None
    string_line_item_id = str(line_item_id)
    if 'gid://' in string_line_item_id:
        return string_line_item_id
    return f"gid://shopify/LineItem/{string_line_item_id}"
