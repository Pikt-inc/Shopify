from .base import (
    ID,
    String,
    Boolean,
    DateTime,
    UnsignedInt64,
    Int,
    Float,
    URL,
)
from .objects import (
    object,
    input_object,
    Order,
    LineItem,
    ProductVariant,
    PageInfo,
    FulfillmentOrderLineItem,
    ShippingLine,
    Fulfillment
)
from .connections import OrderConnection, LineItemConnection, FulfillmentOrderConnection
from .edges import OrderEdge, LineItemEdge, FulfillmentOrderEdge
from .input_objects import (
    OrderIdentifierInput,
    FulfillmentV2Input,
    ProductUnpublishInput,
    OrderInput,
    FulfillmentTrackingInput,
    FulfillmentOrderLineItemsInput,
    FulfillmentOrderLineItemInput
)
from .enums import (
    OrderReturnStatus,
    OrderDisplayFulfillmentStatus,
    OrderDisplayFinancialStatus,
    OrderSortKeys,
    OrderCancelReason,
    ProductVariantInventoryPolicy,
)
from .registry import type_registry

# Resolve forward references for interdependent Pydantic models using the shared registry.
type_registry.rebuild_all()
# Convenience alias for legacy callers expecting a namespace dict.
TYPES_NAMESPACE = type_registry.types

__all__ = [
    "ID",
    "String",
    "Boolean",
    "DateTime",
    "UnsignedInt64",
    "Int",
    "Float",
    "URL",
    "input_object",
    "object",
    "LineItem",
    "PageInfo",
    "Order",
    "ProductVariant",
    "OrderIdentifierInput",
    "OrderReturnStatus",
    "OrderDisplayFulfillmentStatus",
    "OrderDisplayFinancialStatus",
    "OrderSortKeys",
    "OrderCancelReason",
    "ProductVariantInventoryPolicy",
    "LineItemConnection",
    "OrderConnection",
    "FulfillmentOrderConnection",
    "LineItemEdge",
    "OrderEdge",
    "FulfillmentOrderEdge",
    "type_registry",
    "TYPES_NAMESPACE",
    "FulfillmentV2Input",
    "ProductUnpublishInput",
    "OrderInput",
    "FulfillmentTrackingInput",
    "FulfillmentOrderLineItemsInput",
    "FulfillmentOrderLineItem",
    "FulfillmentOrderLineItemInput",
    "ShippingLine",
    "Fulfillment",
]
