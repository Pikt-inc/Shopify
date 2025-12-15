from __future__ import annotations
from typing import TYPE_CHECKING

from .base import edge, String

if TYPE_CHECKING:
    from .objects import Order, LineItem, FulfillmentOrder, FulfillmentOrderLineItem
    from .objects import SalesAgreement, ProductVariant, Publication, ResourcePublication


class OrderEdge(edge):
    node: "Order"

class LineItemEdge(edge):
    node: "LineItem"

class FulfillmentOrderEdge(edge):
    node: "FulfillmentOrder"

class FulfillmentOrderLineItemEdge(edge):
    node: "FulfillmentOrderLineItem"


class SalesAgreementEdge(edge):
    node: "SalesAgreement"


class ProductVariantEdge(edge):
    node: "ProductVariant"


class ResourcePublicationEdge(edge):
    node: "ResourcePublication"


class PublicationEdge(edge):
    node: "Publication"
