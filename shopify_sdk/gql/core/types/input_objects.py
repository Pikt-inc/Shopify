from .objects import input_object
from .enums import (
    ProductStatus,
    ProductVariantInventoryPolicy,
    CombinedListingsRole,
    CountryCode,
)
from .base import (
    ID,
    Boolean,
    String,
    URL,
    Int,
    UnsignedInt64,
    DateTime,
    Float,
)
from typing import List, Optional
from pydantic import Field, field_serializer


class OrderIdentifierInput(input_object):
    id: ID


class OrderCloseInput(input_object):
    id: ID


class OrderOpenInput(input_object):
    id: ID


class OrderMarkAsPaidInput(input_object):
    id: ID


class ProductIdentifierInput(input_object):
    handle: Optional[String]
    id: Optional[ID]


class FileUpdateInput(input_object):
    alt: Optional[String] = Field(default=None)
    filename: Optional[String] = Field(default=None)
    id: ID
    originalSource: Optional[String] = Field(default=None)
    previewImageSource: Optional[String] = Field(default=None)
    referencesToAdd: List[ID] = Field(default_factory=list)
    referencesToRemove: List[ID] = Field(default_factory=list)


class FileSetInput(input_object):
    id: Optional[ID] = Field(default=None)
    originalSource: Optional[String] = Field(default=None)
    contentType: Optional[String] = Field(default=None)
    alt: Optional[String] = Field(default=None)
    filename: Optional[String] = Field(default=None)
    previewImageSource: Optional[String] = Field(default=None)


class FulfillmentTrackingInput(input_object):
    company: String
    number: String
    numbers: List[String] = Field(default_factory=list)
    url: Optional[URL] = Field(default=None)
    urls: List[URL] = Field(default_factory=list)


class FulfillmentOriginAddressInput(input_object):
    address1: String
    address2: String
    city: String
    countryCode: String
    provinceCode: String
    zip: String


class FulfillmentOrderLineItemInput(input_object):
    id: ID
    quantity: Int


class FulfillmentOrderLineItemsInput(input_object):
    fulfillmentOrderId: ID
    fulfillmentOrderLineItems: List[FulfillmentOrderLineItemInput] = Field(
        default_factory=list
    )


class FulfillmentV2Input(input_object):
    lineItemsByFulfillmentOrder: List[FulfillmentOrderLineItemsInput]
    notifyCustomer: Optional[Boolean] = Field(default=None)
    originAddress: Optional[FulfillmentOriginAddressInput] = Field(default=None)
    trackingInfo: Optional[FulfillmentTrackingInput] = Field(default=None)


class FulfillmentInput(input_object):
    lineItemsByFulfillmentOrder: List[FulfillmentOrderLineItemsInput]
    notifyCustomer: Optional[Boolean] = Field(default=None)
    originAddress: Optional[FulfillmentOriginAddressInput] = Field(default=None)
    trackingInfo: Optional[FulfillmentTrackingInput] = Field(default=None)


class ProductPublicationInput(input_object):
    publicationId: ID
    publishDate: Optional[DateTime] = Field(default=None)


class ProductUnpublishInput(input_object):
    id: ID
    productPublications: List[ProductPublicationInput]


class ProductPublishInput(input_object):
    id: ID
    productPublications: List[ProductPublicationInput]


class ProductClaimOwnershipInput(input_object):
    bundles: Optional[Boolean] = Field(default=None)


class OptionCreateInput(input_object):
    name: String
    values: List[String] = Field(default_factory=list)


class SEOInput(input_object):
    description: Optional[String] = Field(default=None)
    title: Optional[String] = Field(default=None)


class OptionValueUpdateInput(input_object):
    id: ID
    name: Optional[String] = Field(default=None)
    linkedMetafieldValue: Optional[String] = Field(default=None)


class OptionValueCreateInput(input_object):
    linkedMetafieldValue: Optional[String] = Field(default=None)
    name: String


class ProductCreateInput(input_object):
    category: Optional[ID] = Field(default=None)
    claimOwnership: Optional[ProductClaimOwnershipInput] = Field(default=None)
    collectionsToJoin: List[ID] = Field(default_factory=list)
    combinedListingRole: Optional[CombinedListingsRole] = Field(default=None)
    descriptionHtml: Optional[String] = Field(default=None)
    giftCard: Optional[Boolean] = Field(default=None)
    giftCardTemplateSuffix: Optional[String] = Field(default=None)
    handle: Optional[String] = Field(default=None)
    metafields: List["MetafieldInput"] = Field(default_factory=list)
    productOptions: List[OptionCreateInput] = Field(default_factory=list)
    productType: Optional[String] = Field(default=None)
    requiresSellingPlan: Optional[Boolean] = Field(default=None)
    seo: Optional[SEOInput] = Field(default=None)
    status: Optional["ProductStatus"] = Field(default=None)
    tags: List[String] = Field(default_factory=list)
    templateSuffix: Optional[String] = Field(default=None)
    title: Optional[String] = Field(default=None)
    vendor: Optional[String] = Field(default=None)


class ProductUpdateInput(input_object):
    category: Optional[ID] = Field(default=None)
    collectionsToJoin: List[ID] = Field(default_factory=list)
    collectionsToLeave: List[ID] = Field(default_factory=list)
    deleteConflictingConstrainedMetafields: Optional[Boolean] = Field(default=None)
    descriptionHtml: Optional[String] = Field(default=None)
    giftCardTemplateSuffix: Optional[String] = Field(default=None)
    handle: Optional[String] = Field(default=None)
    id: ID
    metafields: List["MetafieldInput"] = Field(default_factory=list)
    productType: Optional[String] = Field(default=None)
    redirectNewHandle: Optional[Boolean] = Field(default=None)
    requiresSellingPlan: Optional[Boolean] = Field(default=None)
    seo: Optional[SEOInput] = Field(default=None)
    status: Optional["ProductStatus"] = Field(default=None)
    tags: List[String] = Field(default_factory=list)
    templateSuffix: Optional[String] = Field(default=None)
    title: Optional[String] = Field(default=None)
    vendor: Optional[String] = Field(default=None)


class ProductDeleteInput(input_object):
    id: ID


class DeliveryProvinceInput(input_object):
    code: String


class DeliveryCountryInput(input_object):
    code: Optional["CountryCode"] = Field(default=None)
    restOfWorld: Optional[Boolean] = Field(default=None)
    provinces: Optional[List[DeliveryProvinceInput]] = Field(default=None)
    includeAllProvinces: Optional[Boolean] = Field(default=None)


class MoneyInput(input_object):
    amount: String
    currencyCode: String


class DeliveryRateDefinitionInput(input_object):
    price: MoneyInput
    id: Optional[ID] = Field(default=None)


class DeliveryMethodDefinitionInput(input_object):
    name: Optional[String] = Field(default=None)
    description: Optional[String] = Field(default=None)
    active: Optional[Boolean] = Field(default=None)
    rateDefinition: Optional[DeliveryRateDefinitionInput] = Field(default=None)
    id: Optional[ID] = Field(default=None)


class DeliveryLocationGroupZoneInput(input_object):
    name: Optional[String] = Field(default=None)
    countries: List[DeliveryCountryInput] = Field(default_factory=list)
    methodDefinitionsToCreate: List[DeliveryMethodDefinitionInput] = Field(
        default_factory=list
    )
    id: Optional[ID] = Field(default=None)


class DeliveryProfileLocationGroupInput(input_object):
    locations: List[ID] = Field(default_factory=list)
    zonesToCreate: List[DeliveryLocationGroupZoneInput] = Field(default_factory=list)
    id: Optional[ID] = Field(default=None)


class DeliveryProfileInput(input_object):
    name: Optional[String] = Field(default=None)
    profileLocationGroups: Optional[List[DeliveryProfileLocationGroupInput]] = Field(
        default=None
    )
    locationGroupsToCreate: Optional[List[DeliveryProfileLocationGroupInput]] = Field(
        default=None
    )
    locationGroupsToUpdate: Optional[List[DeliveryProfileLocationGroupInput]] = Field(
        default=None
    )
    locationGroupsToDelete: Optional[List[ID]] = Field(default=None)
    variantsToAssociate: Optional[List[ID]] = Field(default=None)
    variantsToDissociate: Optional[List[ID]] = Field(default=None)
    zonesToDelete: Optional[List[ID]] = Field(default=None)
    methodDefinitionsToDelete: Optional[List[ID]] = Field(default=None)
    conditionsToDelete: Optional[List[ID]] = Field(default=None)
    sellingPlanGroupsToAssociate: Optional[List[ID]] = Field(default=None)
    sellingPlanGroupsToDissociate: Optional[List[ID]] = Field(default=None)


class ProductInput(input_object):
    id: Optional[ID] = Field(default=None)
    title: Optional[String] = Field(default=None)
    descriptionHtml: Optional[String] = Field(default=None)
    handle: Optional[String] = Field(default=None)
    productType: Optional[String] = Field(default=None)
    status: Optional["ProductStatus"] = Field(default=None)
    tags: List[String] = Field(default_factory=list)
    vendor: Optional[String] = Field(default=None)


class InventoryItemInput(input_object):
    sku: Optional[String] = Field(default=None)
    cost: Optional[String] = Field(default=None)
    tracked: Optional[Boolean] = Field(default=None)
    requiresShipping: Optional[Boolean] = Field(default=None)


class InventoryLevelInput(input_object):
    locationId: ID
    availableQuantity: Int


class VariantOptionValueInput(input_object):
    id: Optional[ID] = Field(default=None)
    linkedMetafieldValue: Optional[String] = Field(default=None)
    name: Optional[String] = Field(default=None)
    optionId: Optional[String] = Field(default=None)
    optionName: Optional[String] = Field(default=None)


class UnitPriceMeasurementInput(input_object):
    measuredType: Optional[String] = Field(default=None)
    quantityUnit: Optional[String] = Field(default=None)
    quantityValue: Optional[Float] = Field(default=None)
    referenceUnit: Optional[String] = Field(default=None)
    referenceValue: Optional[Float] = Field(default=None)


class ProductVariantsBulkInput(input_object):
    id: Optional[ID] = Field(default=None)
    price: Optional[String] = Field(default=None)
    compareAtPrice: Optional[String] = Field(default=None)
    barcode: Optional[String] = Field(default=None)
    inventoryItem: Optional[InventoryItemInput] = Field(default=None)
    inventoryPolicy: Optional[ProductVariantInventoryPolicy] = Field(default=None)
    inventoryQuantities: Optional[List[InventoryLevelInput]] = Field(default=None)
    mediaId: Optional[ID] = Field(default=None)
    mediaSrc: List[String] = Field(default_factory=list)
    metafields: List["MetafieldInput"] = Field(default_factory=list)
    optionValues: List[VariantOptionValueInput] = Field(default_factory=list)
    requiresComponents: Optional[Boolean] = Field(default=None)
    showUnitPrice: Optional[Boolean] = Field(default=None)
    taxable: Optional[Boolean] = Field(default=None)
    taxCode: Optional[String] = Field(default=None)
    unitPriceMeasurement: Optional[UnitPriceMeasurementInput] = Field(default=None)


class ProductVariantSetInput(input_object):
    id: Optional[ID] = Field(default=None)
    sku: Optional[String] = Field(default=None)
    price: Optional[String] = Field(default=None)
    compareAtPrice: Optional[String] = Field(default=None)
    barcode: Optional[String] = Field(default=None)
    inventoryPolicy: Optional[ProductVariantInventoryPolicy] = Field(default=None)
    inventoryQuantities: Optional[List[InventoryLevelInput]] = Field(default=None)
    metafields: List["MetafieldInput"] = Field(default_factory=list)
    optionValues: Optional[List[VariantOptionValueInput]] = Field(default=None)


class ProductSetInput(input_object):
    category: Optional[ID] = Field(default=None)
    claimOwnership: Optional[ProductClaimOwnershipInput] = Field(default=None)
    collections: List[ID] = Field(default_factory=list)
    combinedListingRole: Optional[CombinedListingsRole] = Field(default=None)
    title: Optional[String] = Field(default=None)
    descriptionHtml: Optional[String] = Field(default=None)
    files: List[FileSetInput] = Field(default_factory=list)
    giftCard: Optional[Boolean] = Field(default=None)
    giftCardTemplateSuffix: Optional[String] = Field(default=None)
    handle: Optional[String] = Field(default=None)
    productType: Optional[String] = Field(default=None)
    status: Optional["ProductStatus"] = Field(default=None)
    tags: List[String] = Field(default_factory=list)
    vendor: Optional[String] = Field(default=None)
    redirectNewHandle: Optional[Boolean] = Field(default=None)
    requiresSellingPlan: Optional[Boolean] = Field(default=None)
    seo: Optional[SEOInput] = Field(default=None)
    productOptions: Optional[List[OptionCreateInput]] = Field(default=None)
    metafields: List["MetafieldInput"] = Field(default_factory=list)
    templateSuffix: Optional[String] = Field(default=None)
    variants: List[ProductVariantSetInput] = Field(default_factory=list)
    id: Optional[ID] = Field(default=None)


class InventoryChangeInput(input_object):
    inventoryItemId: ID
    locationId: ID
    delta: Int
    ledgerDocumentUri: Optional[String] = Field(default=None)


class InventoryAdjustQuantitiesInput(input_object):
    changes: List[InventoryChangeInput]
    name: String
    reason: String
    referenceDocumentUri: Optional[String] = Field(default=None)


class MailingAddressInput(input_object):
    address1: String
    address2: String
    city: String
    company: String
    countryCode: String
    firstName: String
    lastName: String
    phone: String
    provinceCode: String
    zip: String


class MetafieldInput(input_object):
    id: Optional[ID] = Field(default=None)
    key: String
    namespace: String
    type: String
    value: String


class LocalizedFieldInput(input_object):
    key: String
    value: String


class AttributeInput(input_object):
    key: String
    value: String


class OrderLineItemInput(input_object):
    variantId: Optional[ID] = Field(default=None)
    quantity: Int
    title: Optional[String] = Field(default=None)
    price: Optional[String] = Field(default=None)
    sku: Optional[String] = Field(default=None)
    requiresShipping: Optional[Boolean] = Field(default=None)
    taxable: Optional[Boolean] = Field(default=None)


class OrderCreateLineItemInput(input_object):
    variantId: Optional[ID] = Field(default=None)
    quantity: Int
    title: Optional[String] = Field(default=None)
    price: Optional[String] = Field(default=None)
    sku: Optional[String] = Field(default=None)
    requiresShipping: Optional[Boolean] = Field(default=None)
    taxable: Optional[Boolean] = Field(default=None)


class OrderCreateOrderInput(input_object):
    customAttributes: Optional[AttributeInput] = Field(default=None)
    email: Optional[String] = Field(default=None)
    lineItems: Optional[List[OrderCreateLineItemInput]] = Field(default=None)
    note: Optional[String] = Field(default=None)
    shippingAddress: Optional[MailingAddressInput] = Field(default=None)
    billingAddress: Optional[MailingAddressInput] = Field(default=None)
    tags: List[String] = Field(default_factory=list)
    metafields: Optional[MetafieldInput] = Field(default=None)


class OrderInput(input_object):
    customAttributes: Optional[AttributeInput] = Field(default=None)
    email: Optional[String] = Field(default=None)
    id: ID
    lineItems: Optional[List[OrderLineItemInput]] = Field(default=None)
    localizedFields: Optional[LocalizedFieldInput] = Field(default=None)
    metafields: Optional[MetafieldInput] = Field(default=None)
    note: Optional[String] = Field(default=None)
    shippingAddress: Optional[MailingAddressInput] = Field(default=None)
    tags: List[String] = Field(default_factory=list)


class CreateMediaInput(input_object):
    alt: Optional[String] = Field(default=None)
    mediaContentType: String
    originalSource: String


class StagedUploadInput(input_object):
    resource: String
    filename: String
    mimeType: String
    httpMethod: Optional[String] = Field(default=None)
    fileSize: Optional[UnsignedInt64] = Field(default=None)

    @field_serializer("fileSize")
    def _serialize_file_size(self, value: Optional[UnsignedInt64]) -> Optional[str]:
        if value is None:
            return None
        return str(value)
