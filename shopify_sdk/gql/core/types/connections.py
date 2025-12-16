from __future__ import annotations

from .base import connection
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .edges import (
        CollectionEdge,
        FulfillmentOrderEdge,
        FulfillmentOrderLineItemEdge,
        LineItemEdge,
        LocationEdge,
        OrderEdge,
        ProductBundleComponentEdge,
        ProductVariantEdge,
        PublicationEdge,
        ResourcePublicationEdge,
        SalesAgreementEdge,
    )
    from .objects import (
        Collection,
        FulfillmentOrder,
        FulfillmentOrderLineItem,
        LineItem,
        Location,
        Order,
        PageInfo,
        ProductBundleComponent,
        ProductVariant,
        Publication,
        ResourcePublication,
        SalesAgreement,
    )


class OrderConnection(connection):
    edges: list[OrderEdge]
    nodes: list[Order]
    pageInfo: PageInfo


class ProductVariantConnection(connection):
    edges: list[ProductVariantEdge]
    nodes: list[ProductVariant]
    pageInfo: PageInfo


class LineItemConnection(connection):
    edges: list[LineItemEdge]
    nodes: list[LineItem]
    pageInfo: PageInfo


class FulfillmentOrderConnection(connection):
    edges: list[FulfillmentOrderEdge]
    nodes: list[FulfillmentOrder]
    pageInfo: PageInfo


class FulfillmentOrderLineItemConnection(connection):
    edges: list[FulfillmentOrderLineItemEdge]
    nodes: list[FulfillmentOrderLineItem]
    pageInfo: PageInfo


class SalesAgreementConnection(connection):
    edges: list[SalesAgreementEdge]
    nodes: list[SalesAgreement]
    pageInfo: PageInfo


class ResourcePublicationConnection(connection):
    edges: list[ResourcePublicationEdge]
    nodes: list[ResourcePublication]
    pageInfo: PageInfo


class PublicationConnection(connection):
    edges: list[PublicationEdge]
    nodes: list[Publication]
    pageInfo: PageInfo


class ProductBundleComponentConnection(connection):
    edges: list[ProductBundleComponentEdge]
    nodes: list[ProductBundleComponent]
    pageInfo: PageInfo


class CollectionConnection(connection):
    edges: list[CollectionEdge]
    nodes: list[Collection]
    pageInfo: PageInfo


class LocationConnection(connection):
    edges: list[LocationEdge]
    nodes: list[Location]
    pageInfo: PageInfo
