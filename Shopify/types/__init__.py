from .base import (
    ID,
    String,
    Boolean,
    DateTime,
    UnsignedInt64,
    Int,
    URL,
)
from .objects import (
    object,
    input_object,
    Order,
    OrderLineItem,
    PageInfo,
)
from .connections import OrderLineItemConnection
from .edges import OrderLineItemEdge
from .input_objects import OrderIdentifierInput
from .enums import (
    OrderReturnStatus,
    OrderDisplayFulfillmentStatus,
    OrderDisplayFinancialStatus,
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
    "URL",
    "input_object",
    "object",
    "OrderLineItem",
    "PageInfo",
    "Order",
    "OrderIdentifierInput",
    "OrderReturnStatus",
    "OrderDisplayFulfillmentStatus",
    "OrderDisplayFinancialStatus",
    "OrderLineItemConnection",
    "OrderLineItemEdge",
    "type_registry",
    "TYPES_NAMESPACE",
]
