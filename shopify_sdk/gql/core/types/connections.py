from __future__ import annotations
from typing import TYPE_CHECKING

from .base import connection

if TYPE_CHECKING:
    from .edges import (
        OrderEdge,
        LineItemEdge,
        FulfillmentOrderEdge,
        FulfillmentOrderLineItemEdge,
        SalesAgreementEdge,
        ProductVariantEdge,
        ResourcePublicationEdge,
    )
    from .objects import (
        Order,
        LineItem,
        PageInfo,
        FulfillmentOrder,
        FulfillmentOrderLineItem,
        SalesAgreement,
        ProductVariant,
        ResourcePublication,
    )


class OrderConnection(connection):
    edges: list["OrderEdge"]
    nodes: list["Order"]
    pageInfo: "PageInfo"


class ProductVariantConnection(connection):
    edges: list["ProductVariantEdge"]
    nodes: list["ProductVariant"]
    pageInfo: "PageInfo"


class LineItemConnection(connection):
    edges: list["LineItemEdge"]
    nodes: list["LineItem"]
    pageInfo: "PageInfo"


class FulfillmentOrderConnection(connection):
    edges: list["FulfillmentOrderEdge"]
    nodes: list["FulfillmentOrder"]
    pageInfo: "PageInfo"


class FulfillmentOrderLineItemConnection(connection):
    edges: list["FulfillmentOrderLineItemEdge"]
    nodes: list["FulfillmentOrderLineItem"]
    pageInfo: "PageInfo"


class SalesAgreementConnection(connection):
    edges: list["SalesAgreementEdge"]
    nodes: list["SalesAgreement"]
    pageInfo: "PageInfo"


class ResourcePublicationConnection(connection):
    edges: list["ResourcePublicationEdge"]
    nodes: list["ResourcePublication"]
    pageInfo: "PageInfo"
