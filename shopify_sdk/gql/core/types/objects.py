from __future__ import annotations

from typing import TYPE_CHECKING, List
from .base import (
    Boolean,
    ID,
    String,
    DateTime,
    UnsignedInt64,
    Int,
    Float,
    URL,
    connection,
    AutoRegisterModel,
    Weight,
)
from .enums import (
    OrderReturnStatus,
    OrderDisplayFulfillmentStatus,
    OrderDisplayFinancialStatus,
    FulfillmentOrderStatus,
    ProductVariantInventoryPolicy,
)

if TYPE_CHECKING:
    from .connections import (
        LineItemConnection,
        FulfillmentOrderConnection,
        FulfillmentOrderLineItemConnection
    )


class input_object(AutoRegisterModel):
    def to_graphql(self) -> dict:
        return self.model_dump(exclude_none=True)


class object(AutoRegisterModel):
    pass


class MoneyV2(AutoRegisterModel):
    amount: String
    currencyCode: String


class MoneyBag(AutoRegisterModel):
    presentmentMoney: MoneyV2
    shopMoney: MoneyV2


# Shopify's deprecated Money scalar; keep as string to avoid invalid sub-selections.
Money = String


class Attribute(AutoRegisterModel):
    key: String
    value: String


class DiscountApplication(AutoRegisterModel):
    allocationMethod: String
    targetSelection: String
    targetType: String


class DiscountAllocation(AutoRegisterModel):
    allocatedAmountSet: MoneyBag
    discountApplication: DiscountApplication


class TaxLine(AutoRegisterModel):
    priceSet: MoneyBag
    rate: Float
    ratePercentage: Float
    title: String


class Duty(AutoRegisterModel):
    countryCodeOfOrigin: String
    harmonizedSystemCode: String
    id: ID
    price: MoneyBag
    taxLines: List[TaxLine]


class Image(AutoRegisterModel):
    altText: String
    id: ID
    originalSrc: URL
    transformedSrc: URL


class SelectedOption(AutoRegisterModel):
    name: String
    value: String


class ProductVariantContextualPricing(AutoRegisterModel):
    compareAtPrice: MoneyV2
    price: MoneyV2


class DeliveryProfile(AutoRegisterModel):
    id: ID


class Event(AutoRegisterModel):
    id: ID


class EventEdge(AutoRegisterModel):
    cursor: String
    node: Event


class EventConnection(connection):
    edges: List[EventEdge]
    nodes: List[Event]
    pageInfo: "PageInfo"


class InventoryItem(AutoRegisterModel):
    id: ID
    sku: String


class LineItemGroup(AutoRegisterModel):
    id: ID


class LineItemSellingPlan(AutoRegisterModel):
    name: String
    sellingPlanId: ID


class Product(AutoRegisterModel):
    handle: String
    id: ID
    title: String
    vendor: String


class Media(AutoRegisterModel):
    id: ID
    mediaContentType: String


class MediaEdge(AutoRegisterModel):
    cursor: String
    node: Media


class MediaConnection(connection):
    edges: List[MediaEdge]
    nodes: List[Media]
    pageInfo: "PageInfo"


class Metafield(AutoRegisterModel):
    id: ID
    key: String
    namespace: String
    type: String
    value: String


class MetafieldEdge(AutoRegisterModel):
    cursor: String
    node: Metafield


class MetafieldConnection(connection):
    edges: List[MetafieldEdge]
    nodes: List[Metafield]
    pageInfo: "PageInfo"


class Count(AutoRegisterModel):
    count: Int


class Translation(AutoRegisterModel):
    key: String
    locale: String
    value: String


class UnitPriceMeasurement(AutoRegisterModel):
    measuredType: String
    quantityUnit: String
    quantityValue: Float
    referenceUnit: String
    referenceValue: Float


class ProductEdge(AutoRegisterModel):
    cursor: String
    node: Product


class ProductConnection(connection):
    edges: List[ProductEdge]
    nodes: List[Product]
    pageInfo: "PageInfo"


class ProductVariantComponent(AutoRegisterModel):
    id: ID


class ProductVariantComponentEdge(AutoRegisterModel):
    cursor: String
    node: ProductVariantComponent


class ProductVariantComponentConnection(connection):
    edges: List[ProductVariantComponentEdge]
    nodes: List[ProductVariantComponent]
    pageInfo: "PageInfo"


class SellingPlanGroup(AutoRegisterModel):
    id: ID
    name: String


class SellingPlanGroupEdge(AutoRegisterModel):
    cursor: String
    node: SellingPlanGroup


class SellingPlanGroupConnection(connection):
    edges: List[SellingPlanGroupEdge]
    nodes: List[SellingPlanGroup]
    pageInfo: "PageInfo"


class ProductVariant(AutoRegisterModel):
    availableForSale: Boolean
    barcode: String
    compareAtPrice: Money
    createdAt: DateTime
    defaultCursor: String
    deliveryProfile: DeliveryProfile
    displayName: String
    events: EventConnection
    id: ID
    inventoryItem: InventoryItem
    inventoryPolicy: ProductVariantInventoryPolicy
    inventoryQuantity: Int
    image: Image
    legacyResourceId: UnsignedInt64
    media: MediaConnection
    metafields: MetafieldConnection
    position: Int
    price: Money
    product: Product
    productParents: ProductConnection
    productVariantComponents: ProductVariantComponentConnection
    requiresComponents: Boolean
    selectedOptions: List[SelectedOption]
    sellableOnlineQuantity: Int
    sellingPlanGroups: SellingPlanGroupConnection
    sellingPlanGroupsCount: Count
    showUnitPrice: Boolean
    sku: String
    taxable: Boolean
    title: String
    unitPrice: MoneyV2
    unitPriceMeasurement: UnitPriceMeasurement
    updatedAt: DateTime


class FulfillmentService(AutoRegisterModel):
    handle: String
    id: ID
    serviceName: String


class PageInfo(AutoRegisterModel):
    endCursor: String
    hasNextPage: Boolean
    hasPreviousPage: Boolean
    startCursor: String


class Order(AutoRegisterModel):
    billingAddressMatchesShippingAddress: Boolean
    canMarkAsPaid: Boolean
    canNotifyCustomer: Boolean
    capturable: Boolean
    clientIp: String
    closed: Boolean
    closedAt: DateTime
    confirmationNumber: String
    confirmed: Boolean
    createdAt: DateTime
    displayFulfillmentStatus: OrderDisplayFulfillmentStatus
    displayFinancialStatus: OrderDisplayFinancialStatus
    fulfillable: Boolean
    fulfillmentOrders: FulfillmentOrderConnection
    id: ID
    lineItems: LineItemConnection
    legacyResourceId: String
    merchantEditable: Boolean
    phone: String
    poNumber: String
    paymentGatewayNames: List[String]
    processedAt: DateTime
    productNetwork: Boolean
    refundable: Boolean
    registeredSourceUrl: URL
    requiresShipping: Boolean
    returnStatus: OrderReturnStatus
    sourceIdentifier: String
    sourceName: String
    statusPageUrl: URL
    subtotalLineItemsQuantity: Int
    tags: List[String]
    taxesIncluded: Boolean
    taxExempt: Boolean
    test: Boolean
    totalWeight: Weight
    unpaid: Boolean
    updatedAt: DateTime


class LineItem(AutoRegisterModel):
    currentQuantity: Int
    customAttributes: List[Attribute]
    discountAllocations: List[DiscountAllocation]
    discountedTotalSet: MoneyBag
    discountedUnitPriceAfterAllDiscountsSet: MoneyBag
    discountedUnitPriceSet: MoneyBag
    duties: List[Duty]
    id: ID
    image: Image
    isGiftCard: Boolean
    lineItemGroup: LineItemGroup
    merchantEditable: Boolean
    name: String
    nonFulfillableQuantity: Int
    originalTotalSet: MoneyBag
    originalUnitPriceSet: MoneyBag
    product: Product
    quantity: Int
    refundableQuantity: Int
    requiresShipping: Boolean
    restockable: Boolean
    sellingPlan: LineItemSellingPlan
    sku: String
    taxable: Boolean
    taxLines: List[TaxLine]
    title: String
    totalDiscountSet: MoneyBag
    unfulfilledDiscountedTotalSet: MoneyBag
    unfulfilledOriginalTotalSet: MoneyBag
    unfulfilledQuantity: Int
    variant: ProductVariant
    variantTitle: String
    vendor: String


class FulfillmentOrderLineItem(AutoRegisterModel):
    id: ID
    image: Image
    inventoryItemId: ID
    lineItem: LineItem
    productTitle: String
    remainingQuantity: Int
    requiresShipping: Boolean
    sku: String
    totalQuantity: Int
    variant: ProductVariant
    variantTitle: String
    vendor: String
    weight: Weight


class FulfillmentOrder(AutoRegisterModel):
    channelId: ID
    id: ID
    createdAt: DateTime
    fulfillAt: DateTime
    fulfillBy: DateTime
    status: FulfillmentOrderStatus
    lineItems: FulfillmentOrderLineItemConnection

