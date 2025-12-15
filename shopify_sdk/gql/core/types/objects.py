from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional
from pydantic import Field
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
    OrderCancelReason,
    FulfillmentOrderStatus,
    ProductVariantInventoryPolicy,
    ProductStatus,
)

if TYPE_CHECKING:
    from .connections import (
        LineItemConnection,
        FulfillmentOrderConnection,
        FulfillmentOrderLineItemConnection,
        SalesAgreementConnection,
        ResourcePublicationConnection,
        ProductVariantConnection,
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


class ProductOption(AutoRegisterModel):
    id: Optional[ID] = Field(default=None)
    name: String = Field(default=None)
    position: Int = Field(default=None)
    values: List[String] = Field(default_factory=list)


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
    id: Optional[ID] = Field(default=None)
    sku: String = Field(default=None)
    tracked: Boolean = Field(default=None)
    requiresShipping: Boolean = Field(default=None)
    unitCost: MoneyV2 | None = Field(default=None)


class LineItemGroup(AutoRegisterModel):
    id: ID


class LineItemSellingPlan(AutoRegisterModel):
    name: String
    sellingPlanId: ID


class Product(AutoRegisterModel):
    handle: String = Field(default=None)
    id: ID
    resourcePublications: Optional["ResourcePublicationConnection"] = Field(default=None)
    descriptionHtml: String = Field(default=None)
    productType: String = Field(default=None)
    status: ProductStatus | None = Field(default=None)
    tags: List[String] = Field(default_factory=list)
    title: String = Field(default=None)
    vendor: String = Field(default=None)
    options: List[ProductOption] = Field(default_factory=list)
    variants: "ProductVariantConnection"


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
    availableForSale: Boolean = Field(default=None)
    barcode: String = Field(default=None)
    compareAtPrice: Money = Field(default=None)
    createdAt: DateTime = Field(default=None)
    defaultCursor: String = Field(default=None)
    deliveryProfile: Optional[DeliveryProfile] = Field(default=None)
    displayName: String = Field(default=None)
    events: Optional[EventConnection] = Field(default=None)
    id: Optional[ID] = Field(default=None)
    inventoryItem: InventoryItem | None = Field(default=None)
    inventoryPolicy: Optional[ProductVariantInventoryPolicy] = Field(default=None)
    inventoryQuantity: Int = Field(default=None)
    image: Optional[Image] = Field(default=None)
    legacyResourceId: UnsignedInt64 = Field(default=None)
    media: Optional[MediaConnection] = Field(default=None)
    metafields: Optional[MetafieldConnection] = Field(default=None)
    position: Int = Field(default=None)
    price: Money = Field(default=None)
    product: Product
    productParents: Optional[ProductConnection] = Field(default=None)
    productVariantComponents: Optional[ProductVariantComponentConnection] = Field(default=None)
    requiresComponents: Boolean = Field(default=None)
    requiresShipping: Boolean = Field(default=None)
    selectedOptions: List[SelectedOption] = Field(default_factory=list)
    sellableOnlineQuantity: Int = Field(default=None)
    sellingPlanGroups: Optional[SellingPlanGroupConnection] = Field(default=None)
    sellingPlanGroupsCount: Optional[Count] = Field(default=None)
    showUnitPrice: Boolean = Field(default=None)
    sku: String = Field(default=None)
    taxCode: String = Field(default=None)
    taxable: Boolean = Field(default=None)
    title: String = Field(default=None)
    unitPrice: Optional[MoneyV2] = Field(default=None)
    unitPriceMeasurement: Optional[UnitPriceMeasurement] = Field(default=None)
    updatedAt: DateTime = Field(default=None)


class FulfillmentService(AutoRegisterModel):
    handle: String
    id: ID
    serviceName: String


class PageInfo(AutoRegisterModel):
    endCursor: String
    hasNextPage: Boolean
    hasPreviousPage: Boolean
    startCursor: String


class MailingAddress(AutoRegisterModel):
    address1: String
    address2: String
    city: String
    company: String
    country: String
    countryCodeV2: String
    firstName: String
    lastName: String
    name: String
    phone: String
    province: String
    provinceCode: String
    zip: String


class AdditionalFee(AutoRegisterModel):
    id: ID
    name: String
    price: MoneyBag
    taxLines: List[TaxLine]


class SalesAgreement(AutoRegisterModel):
    happenedAt: DateTime
    id: ID
    


class ResourceAlert(AutoRegisterModel):
    title: String


class OrderApp(AutoRegisterModel):
    id: ID
    name: String


class OrderCancellation(AutoRegisterModel):
    staffNote: String


class ChannelInformation(AutoRegisterModel):
    channelId: ID
    displayName: String
    id: ID


class Customer(AutoRegisterModel):
    id: ID
    displayName: String
    email: String
    firstName: String
    lastName: String
    phone: String


class UTMParameters(AutoRegisterModel):
    campaign: String
    content: String
    medium: String
    source: String
    term: String


class CustomerVisit(AutoRegisterModel):
    occurredAt: DateTime
    landingPage: URL
    referrerUrl: URL
    source: String
    utmParameters: UTMParameters


class CustomerJourneySummary(AutoRegisterModel):
    firstVisit: CustomerVisit
    lastVisit: CustomerVisit
    momentsCount: Int


class DiscountApplicationEdge(AutoRegisterModel):
    cursor: String
    node: DiscountApplication


class DiscountApplicationConnection(connection):
    edges: List[DiscountApplicationEdge]
    nodes: List[DiscountApplication]
    pageInfo: "PageInfo"


class OrderDisputeSummary(AutoRegisterModel):
    disputedAmountSet: MoneyBag
    status: String
    type: String


class FulfillmentTrackingInfo(AutoRegisterModel):
    company: String
    number: String
    url: URL


class Fulfillment(AutoRegisterModel):
    createdAt: DateTime
    id: ID
    status: String
    trackingInfo: List[FulfillmentTrackingInfo]


class LocalizedField(AutoRegisterModel):
    key: String
    locale: String
    value: String


class LocalizedFieldEdge(AutoRegisterModel):
    cursor: String
    node: LocalizedField


class LocalizedFieldConnection(connection):
    edges: List[LocalizedFieldEdge]
    nodes: List[LocalizedField]
    pageInfo: "PageInfo"


class BusinessEntity(AutoRegisterModel):
    id: ID
    name: String
    type: String


class OrderPaymentCollectionDetails(AutoRegisterModel):
    nextPaymentDueAt: DateTime
    outstandingBalance: MoneyBag
    paymentCollectionStatus: String


class PaymentSchedule(AutoRegisterModel):
    amountSet: MoneyBag
    completedAt: DateTime
    dueAt: DateTime


class PaymentTerms(AutoRegisterModel):
    id: ID
    paymentSchedules: List[PaymentSchedule]
    type: String


class Publication(AutoRegisterModel):
    id: ID
    name: String


class ResourcePublication(AutoRegisterModel):
    id: ID
    publication: Publication
    publishDate: DateTime


class Location(AutoRegisterModel):
    address1: String
    address2: String
    city: String
    countryCode: String
    id: ID
    name: String
    province: String
    zip: String


class PurchasingEntity(AutoRegisterModel):
    typename: String = Field(default=None, alias="__typename")


class Refund(AutoRegisterModel):
    createdAt: DateTime
    id: ID
    note: String
    totalRefundedSet: MoneyBag


class Return(AutoRegisterModel):
    createdAt: DateTime
    id: ID
    refunds: List[Refund]
    status: String


class ReturnEdge(AutoRegisterModel):
    cursor: String
    node: Return


class ReturnConnection(connection):
    edges: List[ReturnEdge]
    nodes: List[Return]
    pageInfo: "PageInfo"


class OrderRiskSummary(AutoRegisterModel):
    level: String
    recommendation: String
    score: Float


class ShippingLine(AutoRegisterModel):
    carrierIdentifier: String
    code: String
    currentDiscountedPriceSet: MoneyBag
    custom: Boolean
    deliveryCategory: String
    discountedPriceSet: MoneyBag
    id: ID
    isRemoved: Boolean
    originalPriceSet: MoneyBag
    phone: String
    shippingRateHandle: String
    source: String
    taxLines: List[TaxLine]
    title: String


class ShippingLineEdge(AutoRegisterModel):
    cursor: String
    node: ShippingLine


class ShippingLineConnection(connection):
    edges: List[ShippingLineEdge]
    nodes: List[ShippingLine]
    pageInfo: "PageInfo"


class ShopifyProtectOrderSummary(AutoRegisterModel):
    eligible: Boolean
    protected: Boolean
    status: String


class StaffMember(AutoRegisterModel):
    email: String
    firstName: String
    id: ID
    lastName: String
    name: String


class SuggestedRefund(AutoRegisterModel):
    duties: MoneyBag
    shipping: MoneyBag
    totalRefundAmountSet: MoneyBag


class CashRoundingAdjustment(AutoRegisterModel):
    adjustmentType: String
    amountSet: MoneyBag


class OrderTransaction(AutoRegisterModel):
    accountNumber: String
    amountRoundingSet: MoneyBag
    amountSet: MoneyBag
    authorizationCode: String
    authorizationExpiresAt: DateTime
    createdAt: DateTime
    gateway: String
    id: ID


class Order(AutoRegisterModel):
    additionalFees: List[AdditionalFee]
    agreements: SalesAgreementConnection
    alerts: List[ResourceAlert]
    app: OrderApp
    billingAddress: MailingAddress
    billingAddressMatchesShippingAddress: Boolean
    cancellation: OrderCancellation
    cancelledAt: DateTime
    cancelReason: OrderCancelReason
    canMarkAsPaid: Boolean
    canNotifyCustomer: Boolean
    capturable: Boolean
    cartDiscountAmountSet: MoneyBag
    channelInformation: ChannelInformation
    clientIp: String
    closed: Boolean
    closedAt: DateTime
    confirmationNumber: String
    confirmed: Boolean
    createdAt: DateTime
    currencyCode: String
    currentCartDiscountAmountSet: MoneyBag
    currentShippingPriceSet: MoneyBag
    currentSubtotalLineItemsQuantity: Int
    currentSubtotalPriceSet: MoneyBag
    currentTaxLines: List[TaxLine]
    currentTotalAdditionalFeesSet: MoneyBag
    currentTotalDiscountsSet: MoneyBag
    currentTotalDutiesSet: MoneyBag
    currentTotalPriceSet: MoneyBag
    currentTotalTaxSet: MoneyBag
    currentTotalWeight: UnsignedInt64
    customAttributes: List[Attribute]
    customer: Customer
    customerAcceptsMarketing: Boolean
    customerJourneySummary: CustomerJourneySummary
    customerLocale: String
    discountApplications: DiscountApplicationConnection
    discountCode: String
    discountCodes: List[String]
    displayAddress: MailingAddress
    displayFulfillmentStatus: OrderDisplayFulfillmentStatus
    displayFinancialStatus: OrderDisplayFinancialStatus
    disputes: List[OrderDisputeSummary]
    dutiesIncluded: Boolean
    edited: Boolean
    email: String
    estimatedTaxes: Boolean
    events: EventConnection
    fulfillable: Boolean
    fulfillmentOrders: FulfillmentOrderConnection
    fulfillments: List[Fulfillment]
    fulfillmentsCount: Count
    fullyPaid: Boolean
    hasTimelineComment: Boolean
    id: ID
    lineItems: LineItemConnection
    legacyResourceId: UnsignedInt64
    localizedFields: LocalizedFieldConnection
    merchantBusinessEntity: BusinessEntity
    merchantEditable: Boolean
    merchantEditableErrors: List[String]
    merchantOfRecordApp: OrderApp
    metafield: Metafield
    metafields: MetafieldConnection
    name: String
    netPaymentSet: MoneyBag
    nonFulfillableLineItems: LineItemConnection
    note: String
    number: Int
    originalTotalAdditionalFeesSet: MoneyBag
    originalTotalDutiesSet: MoneyBag
    originalTotalPriceSet: MoneyBag
    paymentCollectionDetails: OrderPaymentCollectionDetails
    paymentGatewayNames: List[String]
    paymentTerms: PaymentTerms
    phone: String
    poNumber: String
    presentmentCurrencyCode: String
    processedAt: DateTime
    productNetwork: Boolean
    publication: Publication
    purchasingEntity: PurchasingEntity
    refundable: Boolean
    refundDiscrepancySet: MoneyBag
    refunds: List[Refund]
    registeredSourceUrl: URL
    requiresShipping: Boolean
    restockable: Boolean
    retailLocation: Location
    returns: ReturnConnection
    returnStatus: OrderReturnStatus
    risk: OrderRiskSummary
    shippingAddress: MailingAddress
    shippingLine: ShippingLine
    shippingLines: ShippingLineConnection
    shopifyProtect: ShopifyProtectOrderSummary
    sourceIdentifier: String
    sourceName: String
    staffMember: StaffMember
    statusPageUrl: URL
    subtotalLineItemsQuantity: Int
    subtotalPriceSet: MoneyBag
    suggestedRefund: SuggestedRefund
    tags: List[String]
    taxesIncluded: Boolean
    taxExempt: Boolean
    taxLines: List[TaxLine]
    test: Boolean
    totalCapturableSet: MoneyBag
    totalCashRoundingAdjustment: CashRoundingAdjustment
    totalDiscountsSet: MoneyBag
    totalOutstandingSet: MoneyBag
    totalPriceSet: MoneyBag
    totalReceivedSet: MoneyBag
    totalRefundedSet: MoneyBag
    totalRefundedShippingSet: MoneyBag
    totalShippingPriceSet: MoneyBag
    totalTaxSet: MoneyBag
    totalTipReceivedSet: MoneyBag
    totalWeight: UnsignedInt64
    transactions: List[OrderTransaction]
    transactionsCount: Count
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
