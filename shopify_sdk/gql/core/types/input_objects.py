from .objects import input_object
from .base import (
    ID,
    Boolean,
    String,
    URL,
    Int,
    DateTime
)
from typing import List, Optional
from pydantic import Field


class OrderIdentifierInput(input_object):
    id: ID
    

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


class ProductInput(input_object):
    id: ID
    status: Optional["ProductStatus"] = Field(default=None)


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
