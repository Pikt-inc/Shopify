from __future__ import annotations


from .base import edge, String

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .objects import *
    from .base import *


class OrderEdge(edge):
    node: Order

class LineItemEdge(edge):
    node: LineItem


class FulfillmentOrderEdge(edge):
    node: FulfillmentOrder


class FulfillmentOrderLineItemEdge(edge):
    node: FulfillmentOrderLineItem


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


class ProductBundleComponentEdge(edge):
    node: ProductBundleComponent


class CollectionEdge(edge):
    node: Collection