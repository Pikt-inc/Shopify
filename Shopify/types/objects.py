from pydantic import BaseModel
from typing import List
from .base import (
    Boolean,
    ID,
    String,
    DateTime,
    UnsignedInt64,
    Int,
    URL
)
from .enums import OrderReturnStatus


class input_object(BaseModel):

    def to_graphql(self) -> dict:
        return self.model_dump(exclude_none=True)


class object(BaseModel):
    pass


class Order(object):
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
    id: ID
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
    totalWeight: UnsignedInt64
    unpaid: Boolean
    updatedAt: DateTime