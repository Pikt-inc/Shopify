from __future__ import annotations

from .base import connection
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .edges import (
        CollectionEdge,
        FulfillmentOrderEdge,
        FulfillmentOrderLineItemEdge,
        FulfillmentLineItemEdge,
        LineItemEdge,
        LocationEdge,
        OrderEdge,
        ProductBundleComponentEdge,
        ProductVariantEdge,
        PublicationEdge,
        RefundLineItemEdge,
        ResourcePublicationEdge,
        SalesAgreementEdge,
        DeliveryProfileEdge,
        ProductEdge,
        OrderTransactionEdge,
        MediaEdge,
    )
    from .objects import (
        Collection,
        FulfillmentOrder,
        FulfillmentOrderLineItem,
        FulfillmentLineItem,
        LineItem,
        Location,
        Order,
        PageInfo,
        ProductBundleComponent,
        ProductVariant,
        Publication,
        RefundLineItem,
        ResourcePublication,
        SalesAgreement,
        DeliveryProfile,
        Product,
        OrderTransaction,
        Media,
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


class FulfillmentLineItemConnection(connection):
    edges: list[FulfillmentLineItemEdge]
    nodes: list[FulfillmentLineItem]
    pageInfo: PageInfo


class RefundLineItemConnection(connection):
    edges: list[RefundLineItemEdge]
    nodes: list[RefundLineItem]
    pageInfo: PageInfo


class OrderTransactionConnection(connection):
    edges: list[OrderTransactionEdge]
    nodes: list[OrderTransaction]
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


class DeliveryProfileConnection(connection):
    edges: list[DeliveryProfileEdge]
    nodes: list[DeliveryProfile]
    pageInfo: PageInfo


class ProductConnection(connection):
    edges: list[ProductEdge]
    nodes: list[Product]
    pageInfo: PageInfo


class MediaConnection(connection):
    edges: list[MediaEdge]
    nodes: list[Media]
    pageInfo: "PageInfo"
