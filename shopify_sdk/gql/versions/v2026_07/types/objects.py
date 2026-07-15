from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union
from pydantic import Field

from shopify_sdk.gql.core.types.base import *

if TYPE_CHECKING:
    from .connections import (
        CollectionConnection,
        FulfillmentOrderConnection,
        FulfillmentOrderLineItemConnection,
        FulfillmentLineItemConnection,
        LineItemConnection,
        ProductConnection,
        ProductBundleComponentConnection,
        ProductVariantConnection,
        PublicationConnection,
        RefundLineItemConnection,
        ResourcePublicationConnection,
        SalesAgreementConnection,
        OrderTransactionConnection,
        MediaConnection,
        DeliveryMethodDefinitionConnection,
        DeliveryLocationGroupZoneConnection,
        DeliveryProfileItemConnection,
        SellingPlanGroupConnection,
        LocationConnection,
    )
    from .enums import *


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


class Attribute(AutoRegisterModel):
    key: String
    value: String


class DiscountApplication(AutoRegisterModel):
    allocationMethod: String
    targetSelection: String
    targetType: String


# GraphQL often returns formatted strings; alias to simple String for typing.
FormattedString = String


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
    altText: Optional[String] = Field(default=None)
    height: Optional[Int] = Field(default=None)
    id: ID
    url: URL
    width: Optional[Int] = Field(default=None)


class SelectedOption(AutoRegisterModel):
    name: String
    value: String


class ProductOption(AutoRegisterModel):
    id: ID
    name: String
    position: Int
    values: List[String]


class ProductVariantContextualPricing(AutoRegisterModel):
    compareAtPrice: MoneyV2
    price: MoneyV2


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
    countryCodeOfOrigin: Optional[CountryCode] = Field(default=None)
    countryHarmonizedSystemCodes: "CountryHarmonizedSystemCodeConnection"
    createdAt: DateTime
    duplicateSkuCount: Int
    harmonizedSystemCode: Optional[String] = Field(default=None)
    id: ID
    inventoryHistoryUrl: Optional[URL] = Field(default=None)
    inventoryLevel: Optional["InventoryLevel"] = Field(default=None)
    inventoryLevels: "InventoryLevelConnection"
    legacyResourceId: UnsignedInt64
    locationsCount: Optional[Count] = Field(default=None)
    measurement: "InventoryItemMeasurement"
    provinceCodeOfOrigin: Optional[String] = Field(default=None)
    requiresShipping: Boolean
    sku: Optional[String] = Field(default=None)
    tracked: Boolean
    trackedEditable: "EditableProperty"
    unitCost: Optional[MoneyV2] = Field(default=None)
    updatedAt: DateTime
    variant: ProductVariant


class LineItemGroup(AutoRegisterModel):
    id: ID


class InventoryLevel(AutoRegisterModel):
    canDeactivate: Boolean
    createdAt: DateTime
    deactivationAlert: Optional[String] = Field(default=None)
    id: ID
    item: InventoryItem
    location: "Location"
    quantities: List["InventoryQuantity"]
    scheduledChanges: "InventoryScheduledChangeConnection"
    updatedAt: DateTime


class InventoryLevelEdge(AutoRegisterModel):
    cursor: String
    node: InventoryLevel


class InventoryLevelConnection(connection):
    edges: List[InventoryLevelEdge]
    nodes: List[InventoryLevel]
    pageInfo: "PageInfo"


class LineItemSellingPlan(AutoRegisterModel):
    name: String
    sellingPlanId: ID


class SEO(AutoRegisterModel):
    description: String
    title: String


class TaxonomyCategory(AutoRegisterModel):
    ancestorIds: List[ID]
    childrenIds: List[ID]
    fullName: String
    id: ID
    isArchived: Boolean
    isLeaf: Boolean
    isRoot: Boolean
    level: Int
    parentId: Optional[ID] = Field(default=None)


class ProductPriceRangeV2(AutoRegisterModel):
    maxVariantPrice: MoneyV2
    minVariantPrice: MoneyV2


class ComponentizedProductsBundleConsolidatedOptionSelectionComponent(
    AutoRegisterModel
):
    optionId: ID
    value: String


class ComponentizedProductsBundleConsolidatedOptionSelection(AutoRegisterModel):
    components: List[ComponentizedProductsBundleConsolidatedOptionSelectionComponent]
    value: String


class ComponentizedProductsBundleConsolidatedOption(AutoRegisterModel):
    name: String
    selections: List[ComponentizedProductsBundleConsolidatedOptionSelection]


class Product(AutoRegisterModel):
    availablePublicationsCount: Optional[Count] = Field(default=None)
    bundleComponents: ProductBundleComponentConnection
    bundleConsolidatedOptions: Optional[
        List[ComponentizedProductsBundleConsolidatedOption]
    ] = Field(default=None)
    category: Optional[TaxonomyCategory] = Field(default=None)
    collections: "CollectionConnection"
    combinedListingRole: Optional["CombinedListingsRole"] = Field(default=None)
    createdAt: DateTime
    defaultCursor: String
    description: String
    descriptionHtml: String
    events: EventConnection
    featuredMedia: Optional[Media] = Field(default=None)
    giftCardTemplateSuffix: Optional[String] = Field(default=None)
    handle: String
    hasOnlyDefaultVariant: Boolean
    hasOutOfStockVariants: Boolean
    hasVariantsThatRequiresComponents: Boolean
    id: ID
    inCollection: Boolean
    isGiftCard: Boolean
    legacyResourceId: UnsignedInt64
    media: MediaConnection
    mediaCount: Optional[Count] = Field(default=None)
    metafield: Optional[Metafield] = Field(default=None)
    metafields: MetafieldConnection
    onlineStorePreviewUrl: Optional[URL] = Field(default=None)
    onlineStoreUrl: Optional[URL] = Field(default=None)
    options: List[ProductOption]
    priceRangeV2: ProductPriceRangeV2
    productComponentsCount: Optional[Count] = Field(default=None)
    productParents: ProductConnection
    productType: String
    publishedAt: Optional[DateTime] = Field(default=None)
    publishedInContext: Boolean
    publishedOnCurrentPublication: Boolean
    publishedOnPublication: Boolean
    requiresSellingPlan: Boolean
    resourcePublications: "ResourcePublicationConnection"
    resourcePublicationsCount: Optional[Count] = Field(default=None)
    sellingPlanGroups: SellingPlanGroupConnection
    sellingPlanGroupsCount: Optional[Count] = Field(default=None)
    seo: SEO
    status: ProductStatus
    tags: List[String]
    templateSuffix: Optional[String] = Field(default=None)
    title: String
    totalInventory: Int
    tracksInventory: Boolean
    translations: List[Translation]
    unpublishedPublications: "PublicationConnection"
    updatedAt: DateTime
    variants: "ProductVariantConnection"
    variantsCount: Optional[Count] = Field(default=None)
    vendor: String


class MediaError(AutoRegisterModel):
    code: "MediaErrorCode"
    details: Optional[String] = Field(default=None)
    message: String


class MediaWarning(AutoRegisterModel):
    code: MediaWarningCode
    message: Optional[String] = Field(default=None)


class MediaPreviewImage(AutoRegisterModel):
    image: Optional[Image] = Field(default=None)
    status: MediaStatus


class Media(AutoRegisterModel):
    alt: Optional[String] = Field(default=None)
    id: ID
    mediaContentType: String
    mediaErrors: List[MediaError]
    mediaWarnings: List[MediaWarning]
    preview: Optional[MediaPreviewImage] = Field(default=None)
    status: String


class Metafield(AutoRegisterModel):
    id: ID
    key: String
    namespace: String
    type: String
    value: String


class MetafieldCapabilityUniqueValues(AutoRegisterModel):
    """Expose whether unique metafield values are eligible and enabled."""

    eligible: Boolean
    enabled: Boolean


class MetafieldCapabilities(AutoRegisterModel):
    """Expose metafield definition capabilities needed for custom IDs."""

    uniqueValues: MetafieldCapabilityUniqueValues


class MetafieldDefinitionType(AutoRegisterModel):
    """Expose the Shopify metafield type name."""

    name: String


class MetafieldDefinition(AutoRegisterModel):
    """Typed projection used to validate a product custom-ID definition."""

    id: ID
    key: String
    namespace: String
    ownerType: "MetafieldOwnerType"
    type: MetafieldDefinitionType
    capabilities: MetafieldCapabilities


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


class CountryHarmonizedSystemCode(AutoRegisterModel):
    id: ID
    countryCode: CountryCode
    harmonizedSystemCode: String


class CountryHarmonizedSystemCodeEdge(AutoRegisterModel):
    cursor: String
    node: CountryHarmonizedSystemCode


class CountryHarmonizedSystemCodeConnection(connection):
    edges: List[CountryHarmonizedSystemCodeEdge]
    nodes: List[CountryHarmonizedSystemCode]
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


class ProductVariant(AutoRegisterModel):
    availableForSale: Boolean
    barcode: Optional[String] = Field(default=None)
    compareAtPrice: Optional[Money] = Field(default=None)
    contextualPricing: ProductVariantContextualPricing
    createdAt: DateTime
    defaultCursor: String
    deliveryProfile: Optional[DeliveryProfile] = Field(default=None)
    displayName: String
    events: EventConnection
    id: ID
    inventoryItem: InventoryItem
    inventoryPolicy: ProductVariantInventoryPolicy
    inventoryQuantity: Optional[Int] = Field(default=None)
    image: Optional[Image] = Field(default=None)
    legacyResourceId: UnsignedInt64
    media: MediaConnection
    metafield: Optional[Metafield] = Field(default=None)
    metafields: MetafieldConnection
    position: Int
    price: Money
    product: Product
    productParents: ProductConnection
    productVariantComponents: ProductVariantComponentConnection
    requiresComponents: Boolean = Field(default=False)
    requiresShipping: Boolean
    selectedOptions: List[SelectedOption] = Field(default_factory=list)
    sellableOnlineQuantity: Int
    sellingPlanGroups: SellingPlanGroupConnection
    sellingPlanGroupsCount: Optional[Count] = Field(default=None)
    showUnitPrice: Boolean
    sku: Optional[String] = Field(default=None)
    taxCode: Optional[String] = Field(default=None)
    taxable: Boolean
    title: String
    translations: List[Translation] = Field(default_factory=list)
    unitPrice: Optional[MoneyV2] = Field(default=None)
    unitPriceMeasurement: Optional[UnitPriceMeasurement] = Field(default=None)
    updatedAt: DateTime


class FulfillmentService(AutoRegisterModel):
    handle: String
    id: ID
    serviceName: String


class PageInfo(AutoRegisterModel):
    endCursor: Optional[String] = Field(default=None)
    hasNextPage: Boolean
    hasPreviousPage: Boolean
    startCursor: Optional[String] = Field(default=None)


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
    fulfillmentLineItems: FulfillmentLineItemConnection
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
    isPublished: Boolean
    publication: Publication
    publishDate: DateTime


class LocationAddress(AutoRegisterModel):
    address1: Optional[String] = Field(default=None)
    address2: Optional[String] = Field(default=None)
    city: Optional[String] = Field(default=None)
    country: Optional[String] = Field(default=None)
    countryCode: Optional[String] = Field(default=None)
    formatted: List[String] = Field(default_factory=list)
    latitude: Optional[Float] = Field(default=None)
    longitude: Optional[Float] = Field(default=None)
    phone: Optional[String] = Field(default=None)
    province: Optional[String] = Field(default=None)
    provinceCode: Optional[String] = Field(default=None)
    zip: Optional[String] = Field(default=None)


class Location(AutoRegisterModel):
    activatable: Boolean
    address: LocationAddress
    addressVerified: Boolean
    createdAt: DateTime
    deactivatable: Boolean
    deactivatedAt: Optional[DateTime] = Field(default=None)
    deletable: Boolean
    fulfillmentService: Optional[FulfillmentService] = Field(default=None)
    fulfillsOnlineOrders: Boolean
    hasActiveInventory: Boolean
    hasUnfulfilledOrders: Boolean
    id: ID
    name: String


class PurchasingEntity(AutoRegisterModel):
    typename: Optional[String] = Field(default=None, alias="__typename")


class RefundLineItem(AutoRegisterModel):
    lineItem: LineItem
    quantity: Int
    subtotalSet: MoneyBag


class Refund(AutoRegisterModel):
    createdAt: DateTime
    id: ID
    note: String
    refundLineItems: RefundLineItemConnection
    totalRefundedSet: MoneyBag
    transactions: OrderTransactionConnection


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
    kind: String
    processedAt: DateTime
    status: String


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
    fulfillmentStatus: String
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


class FulfillmentLineItem(AutoRegisterModel):
    lineItem: LineItem
    quantity: Int


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


class ProductBundleComponentOptionSelectionValue(AutoRegisterModel):
    selectionStatus: ProductBundleComponentOptionSelectionStatus
    value: String


class ProductBundleComponentQuantityOption(AutoRegisterModel):
    name: String
    parentOption: Optional[ProductOption] = Field(default=None)
    values: ProductBundleComponentOptionSelectionValue


class ProductBundleComponentOptionSelection(AutoRegisterModel):
    componentOption: ProductOption
    parentOption: Optional[ProductOption] = Field(default=None)
    values: List[ProductBundleComponentOptionSelectionValue]


class ProductBundleComponent(AutoRegisterModel):
    componentProduct: Product
    componentVariants: ProductVariantConnection
    componentVariantsCount: Count
    optionSelections: List[ProductBundleComponentOptionSelection]
    quantity: Int
    quantityOption: ProductBundleComponentQuantityOption


class Collection(AutoRegisterModel):
    availablePublicationsCount: Optional[Count] = Field(default=None)
    description: String
    descriptionHtml: String
    handle: String
    hasProducts: Boolean
    id: ID
    image: Optional[Image] = Field(default=None)
    productsCount: Optional[Count] = Field(default=None)


class InventoryQuantity(AutoRegisterModel):
    id: ID
    name: String
    quantity: Int
    updatedAt: Optional[DateTime] = Field(default=None)


class InventoryChange(AutoRegisterModel):
    delta: Int
    name: String
    quantityAfterChange: Optional[Int] = Field(default=None)


class InventoryAdjustmentGroup(AutoRegisterModel):
    id: ID
    changes: List[InventoryChange]
    createdAt: DateTime
    reason: String
    referenceDocumentUri: Optional[String] = Field(default=None)


class InventorySetQuantitiesUserError(AutoRegisterModel):
    code: Optional[String] = Field(default=None)
    field: Optional[List[String]] = Field(default=None)
    message: String


class InventoryItemMeasurement(AutoRegisterModel):
    id: ID
    weight: Optional[Weight] = Field(default=None)


class EditableProperty(AutoRegisterModel):
    locked: Boolean
    reason: Optional[FormattedString] = Field(default=None)


class InventoryScheduledChange(AutoRegisterModel):
    id: ID
    effectiveAt: DateTime
    createdAt: DateTime
    quantities: List[InventoryQuantity]


class InventoryScheduledChangeEdge(AutoRegisterModel):
    cursor: String
    node: InventoryScheduledChange


class InventoryScheduledChangeConnection(connection):
    edges: List[InventoryScheduledChangeEdge]
    nodes: List[InventoryScheduledChange]
    pageInfo: "PageInfo"


class BulkOperation(AutoRegisterModel):
    completedAt: Optional[DateTime] = Field(default=None)
    createdAt: DateTime
    errorCode: Optional[String] = Field(default=None)
    fileSize: Optional[UnsignedInt64] = Field(default=None)
    id: ID
    objectCount: Optional[UnsignedInt64] = Field(default=None)
    partialDataUrl: Optional[URL] = Field(default=None)
    query: String
    status: BulkOperationStatus
    type: BulkOperationType
    url: Optional[URL] = Field(default=None)


class Job(AutoRegisterModel):
    done: Boolean
    id: ID


class ProductSetUserError(AutoRegisterModel):
    code: ProductSetUserErrorCode
    field: Optional[List[String]] = Field(default=None)
    message: String


class OrderCancelUserError(AutoRegisterModel):
    code: Optional[OrderCancelUserErrorCode] = Field(default=None)
    field: Optional[List[String]] = Field(default=None)
    message: String


class ProductSetOperation(AutoRegisterModel):
    id: ID
    status: String
    product: Optional[Product] = Field(default=None)
    userErrors: List[ProductSetUserError]


class ProductSetPayload(AutoRegisterModel):
    product: Optional[Product] = Field(default=None)
    productSetOperation: Optional[ProductSetOperation] = Field(default=None)
    userErrors: List[ProductSetUserError]


class UserError(AutoRegisterModel):
    field: Optional[List[String]] = Field(default=None)
    message: String


class WebhookSubscription(AutoRegisterModel):
    filter: Optional[String] = Field(default=None)
    format: Optional[String] = Field(default=None)
    id: ID
    includeFields: List[String] = Field(default_factory=list)
    metafieldNamespaces: List[String] = Field(default_factory=list)
    name: Optional[String] = Field(default=None)
    topic: String
    uri: URL


class BulkOperationUserError(AutoRegisterModel):
    code: Optional[BulkOperationUserErrorCode] = Field(default=None)
    field: Optional[List[String]] = Field(default=None)
    message: String


class Shop(AutoRegisterModel):
    checkoutApiSupported: Boolean
    createdAt: DateTime
    description: String
    email: String
    id: ID


class StagedUploadParameter(AutoRegisterModel):
    name: String
    value: String


class StagedMediaUploadTarget(AutoRegisterModel):
    parameters: List[StagedUploadParameter]
    resourceUrl: Optional[URL]
    url: Optional[URL]


class ShippingRate(AutoRegisterModel):
    handle: String
    price: MoneyV2
    title: String


class DeliveryProfile(AutoRegisterModel):
    activeMethodDefinitionsCount: Int
    default: Boolean
    id: ID
    locationsWithoutRatesCount: Int
    name: String
    originLocationCount: Int
    productVariantsCount: Optional[Count] = Field(default=None)
    unassignedLocations: List[Location]
    version: Int
    zoneCountryCount: Int
    profileItems: DeliveryProfileItemConnection
    profileLocationGroups: List[DeliveryProfileLocationGroup]
    sellingPlanGroups: SellingPlanGroupConnection
    unassignedLocationsPaginated: "LocationConnection"


class DeliveryProvince(AutoRegisterModel):
    code: String
    id: ID
    name: String
    translatedName: String


class DeliveryCountryCodeOrRestOfWorld(AutoRegisterModel):
    countryCode: Optional[CountryCode] = Field(default=None)
    restOfWorld: Boolean


class DeliveryCountry(AutoRegisterModel):
    code: DeliveryCountryCodeOrRestOfWorld
    id: ID
    name: String
    provinces: List[DeliveryProvince]
    translatedName: String


class DeliveryZone(AutoRegisterModel):
    countries: List[DeliveryCountry]
    id: ID
    name: String


# Alias for GraphQL union: DeliveryConditionCriteria = MoneyV2 | Weight
DeliveryConditionCriteria = MoneyV2 | Weight


class DeliveryCondition(AutoRegisterModel):
    conditionCriteria: DeliveryConditionCriteria
    field: "DeliveryConditionField"
    id: ID
    operator: "DeliveryConditionOperator"


class DeliveryRateDefinition(AutoRegisterModel):
    price: MoneyV2
    id: ID


class DeliveryParticipant(AutoRegisterModel):
    id: ID


class DeliveryMethodDefinition(AutoRegisterModel):
    active: Boolean
    description: Optional[String] = Field(default=None)
    id: ID
    methodConditions: List[DeliveryCondition]
    name: String
    rateProvider: Union[DeliveryRateDefinition, DeliveryParticipant]


class DeliveryMethodDefinitionCounts(AutoRegisterModel):
    participantDefinitionsCount: Int
    rateDefinitionsCount: Int


class DeliveryLocationGroupZone(AutoRegisterModel):
    methodDefinitionCounts: DeliveryMethodDefinitionCounts
    methodDefinitions: DeliveryMethodDefinitionConnection
    zone: DeliveryZone


class DeliveryCountryAndZone(AutoRegisterModel):
    country: DeliveryCountry
    zone: DeliveryZone


class DeliveryLocationGroup(AutoRegisterModel):
    id: ID
    locations: LocationConnection


class DeliveryProfileLocationGroup(AutoRegisterModel):
    countriesInAnyZone: List[DeliveryCountryAndZone]
    locationGroup: DeliveryLocationGroup
    locationGroupZones: DeliveryLocationGroupZoneConnection


class DeliveryProfileItem(AutoRegisterModel):
    id: ID
    product: Optional[Product] = Field(default=None)
    variants: Optional[ProductVariantConnection] = Field(default=None)
