from .objects import input_object
from .enums import ProductStatus, ProductVariantInventoryPolicy, CombinedListingsRole
from .base import (
    ID,
    Boolean,
    String,
    URL,
    Int,
    DateTime,
    Float,
)
from typing import Any, List, Optional
from pydantic import Field


class OrderIdentifierInput(input_object):
    id: ID


class ProductIdentifierInput(input_object):
    handle: String | None
    id: Optional[ID]
    

class FulfillmentTrackingInput(input_object):
    company: String
    number: String
    numbers: List[String] = Field(default_factory=list)
    url: URL = Field(default=None)
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
    fulfillmentOrderLineItems: List[FulfillmentOrderLineItemInput] = Field(default_factory=list)


class FulfillmentV2Input(input_object):
    lineItemsByFulfillmentOrder: List[FulfillmentOrderLineItemsInput]
    notifyCustomer: Boolean = Field(default=None)
    originAddress: Optional[FulfillmentOriginAddressInput] = Field(default=None)
    trackingInfo: Optional[FulfillmentTrackingInput] = Field(default=None)

class ProductPublicationInput(input_object):
    publicationId: ID
    publishDate: DateTime = Field(default=None)


class ProductUnpublishInput(input_object):
    id: ID
    productPublications: List[ProductPublicationInput]


class ProductPublishInput(input_object):
    id: ID
    productPublications: List[ProductPublicationInput]


class ProductClaimOwnershipInput(input_object):
    bundles: Boolean = Field(default=None)


class OptionCreateInput(input_object):
    name: String
    values: List[String] = Field(default_factory=list)


class SEOInput(input_object):
    description: String = Field(default=None)
    title: String = Field(default=None)


class ProductCreateInput(input_object):
    category: Optional[ID] = Field(default=None)
    claimOwnership: Optional[ProductClaimOwnershipInput] = Field(default=None)
    collectionsToJoin: List[ID] = Field(default_factory=list)
    combinedListingRole: Optional[CombinedListingsRole] = Field(default=None)
    descriptionHtml: String = Field(default=None)
    giftCard: Boolean = Field(default=None)
    giftCardTemplateSuffix: String = Field(default=None)
    handle: String = Field(default=None)
    metafields: List["MetafieldInput"] = Field(default_factory=list)
    productOptions: List[OptionCreateInput] = Field(default_factory=list)
    productType: String = Field(default=None)
    requiresSellingPlan: Boolean = Field(default=None)
    seo: Optional[SEOInput] = Field(default=None)
    status: Optional["ProductStatus"] = Field(default=None)
    tags: List[String] = Field(default_factory=list)
    templateSuffix: String = Field(default=None)
    title: String = Field(default=None)
    vendor: String = Field(default=None)


class ProductUpdateInput(input_object):
    category: Optional[ID] = Field(default=None)
    collectionsToJoin: List[ID] = Field(default_factory=list)
    collectionsToLeave: List[ID] = Field(default_factory=list)
    deleteConflictingConstrainedMetafields: Boolean = Field(default=None)
    descriptionHtml: String = Field(default=None)
    giftCardTemplateSuffix: String = Field(default=None)
    handle: String = Field(default=None)
    id: ID
    metafields: List["MetafieldInput"] = Field(default_factory=list)
    productType: String = Field(default=None)
    redirectNewHandle: Boolean = Field(default=None)
    requiresSellingPlan: Boolean = Field(default=None)
    seo: Optional[SEOInput] = Field(default=None)
    status: Optional["ProductStatus"] = Field(default=None)
    tags: List[String] = Field(default_factory=list)
    templateSuffix: String = Field(default=None)
    title: String = Field(default=None)
    vendor: String = Field(default=None)


class ProductInput(input_object):
    id: Optional[ID] = Field(default=None)
    title: String = Field(default=None)
    descriptionHtml: String = Field(default=None)
    handle: String = Field(default=None)
    productType: String = Field(default=None)
    status: Optional["ProductStatus"] = Field(default=None)
    tags: List[String] = Field(default_factory=list)
    vendor: String = Field(default=None)


class InventoryItemInput(input_object):
    sku: String = Field(default=None)
    cost: String = Field(default=None)
    tracked: Boolean = Field(default=None)
    requiresShipping: Boolean = Field(default=None)


class InventoryLevelInput(input_object):
    locationId: ID
    availableQuantity: Int


class VariantOptionValueInput(input_object):
    id: Optional[ID] = Field(default=None)
    linkedMetafieldValue: String = Field(default=None)
    name: String = Field(default=None)
    optionId: String = Field(default=None)
    optionName: String = Field(default=None)


class UnitPriceMeasurementInput(input_object):
    measuredType: String = Field(default=None)
    quantityUnit: String = Field(default=None)
    quantityValue: Float = Field(default=None)
    referenceUnit: String = Field(default=None)
    referenceValue: Float = Field(default=None)


class ProductVariantsBulkInput(input_object):
    id: Optional[ID] = Field(default=None)
    price: String = Field(default=None)
    compareAtPrice: String = Field(default=None)
    barcode: String = Field(default=None)
    inventoryItem: Optional[InventoryItemInput] = Field(default=None)
    inventoryPolicy: Optional[ProductVariantInventoryPolicy] = Field(default=None)
    inventoryQuantities: Optional[List[InventoryLevelInput]] = Field(default=None)
    mediaId: Optional[ID] = Field(default=None)
    mediaSrc: List[String] = Field(default_factory=list)
    metafields: List["MetafieldInput"] = Field(default_factory=list)
    optionValues: List[VariantOptionValueInput] = Field(default_factory=list)
    requiresComponents: Boolean = Field(default=None)
    showUnitPrice: Boolean = Field(default=None)
    taxable: Boolean = Field(default=None)
    taxCode: String = Field(default=None)
    unitPriceMeasurement: Optional[UnitPriceMeasurementInput] = Field(default=None)


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
    id: ID
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


class OrderInput(input_object):
    customAttributes: Optional[AttributeInput] = Field(default=None)
    email: Optional[String] = Field(default=None)
    id: ID
    localizedFields: Optional[LocalizedFieldInput] = Field(default=None)
    metafields: Optional[MetafieldInput] = Field(default=None)
    note: Optional[String] = Field(default=None)
    shippingAddress: Optional[MailingAddressInput] = Field(default=None)
    tags: List[String] = Field(default_factory=list)
