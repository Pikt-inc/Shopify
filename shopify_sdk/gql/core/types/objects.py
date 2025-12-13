from __future__ import annotations

from typing import TYPE_CHECKING, List
from .base import (
    Boolean,
    ID,
    String,
    DateTime,
    UnsignedInt64,
    Int,
    URL,
    AutoRegisterModel,
)
from .enums import (
    OrderReturnStatus,
    OrderDisplayFulfillmentStatus,
    OrderDisplayFinancialStatus,
    FulfillmentOrderStatus
)

if TYPE_CHECKING:
    from .connections import LineItemConnection, FulfillmentOrderConnection


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
    totalWeight: UnsignedInt64
    unpaid: Boolean
    updatedAt: DateTime

class LineItem(AutoRegisterModel):
    currentQuantity: Int
    quantity: Int
    title: String
    id: ID
    sku: String
    originalTotalSet: MoneyBag
    originalUnitPriceSet: MoneyBag

class FulfillmentOrder(AutoRegisterModel):
    channelId: ID
    id: ID
    createdAt: DateTime
    fulfillAt: DateTime
    fulfillBy: DateTime
    status: FulfillmentOrderStatus
