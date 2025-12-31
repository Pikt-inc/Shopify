from __future__ import annotations


from .base import edge

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .objects import (
        Collection,
        FulfillmentOrder,
        FulfillmentOrderLineItem,
        FulfillmentLineItem,
        LineItem,
        Location,
        Order,
        ProductBundleComponent,
        ProductVariant,
        Publication,
        RefundLineItem,
        ResourcePublication,
        SalesAgreement,
        Product,
        DeliveryProfile,
        OrderTransaction,
        Media
    )


class OrderEdge(edge):
    node: Order


class LineItemEdge(edge):
    node: LineItem


class FulfillmentOrderEdge(edge):
    node: FulfillmentOrder


class FulfillmentOrderLineItemEdge(edge):
    node: FulfillmentOrderLineItem


class FulfillmentLineItemEdge(edge):
    node: FulfillmentLineItem


class RefundLineItemEdge(edge):
    node: RefundLineItem


class OrderTransactionEdge(edge):
    node: OrderTransaction


class SalesAgreementEdge(edge):
    node: SalesAgreement


class ProductVariantEdge(edge):
    node: ProductVariant


class ResourcePublicationEdge(edge):
    node: ResourcePublication


class PublicationEdge(edge):
    node: Publication


class ProductBundleComponentEdge(edge):
    node: ProductBundleComponent


class CollectionEdge(edge):
    node: Collection


class LocationEdge(edge):
    node: Location


class ProductEdge(edge):
    node: Product


class DeliveryProfileEdge(edge):
    node: DeliveryProfile


class MediaEdge(edge):
    node: Media