from .objects import input_object
from .base import (
    ID,
    Boolean,
    String,
    URL,
    Int,
)
from typing import List


class OrderIdentifierInput(input_object):
    id: ID
    

class FulfillmentTrackingInput(input_object):
    company: String
    number: String
    numbers: List[String]
    url: URL
    urls: List[URL]


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
    fulfillmentOrderLineItems: List[FulfillmentOrderLineItemInput]


class FulfillmentV2Input(input_object):
    lineItemsByFulfillmentOrder: List[FulfillmentOrderLineItemsInput]
    notifyCustomer: Boolean
    originAddress: FulfillmentOriginAddressInput
    trackingInfo: FulfillmentTrackingInput
