from .base import enum

class OrderReturnStatus(enum):
    IN_PROGRESS = "IN_PROGRESS"
    INSPECTION_COMPLETE = "INSPECTION_COMPLETE"
    NO_RETURN = "NO_RETURN"
    RETURN_FAILED = "RETURN_FAILED"
    RETURN_REQUESTED = "RETURN_REQUESTED"
    RETURNED = "RETURNED"

class OrderDisplayFulfillmentStatus(enum):
    FULFILLED = "FULFILLED"
    IN_PROGRESS = "IN_PROGRESS"
    ON_HOLD = "ON_HOLD"
    OPEN = "OPEN"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    PENDING_FULFILLMENT = "PENDING_FULFILLMENT"
    RESTOCKED = "RESTOCKED"
    SCHEDULED = "SCHEDULED"
    UNFULFILLED = "UNFULFILLED"

class OrderDisplayFinancialStatus(enum):
    AUTHORIZED = "AUTHORIZED"
    PAID = "PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    PENDING = "PENDING"
    REFUNDED = "REFUNDED"
    VOIDED = "VOIDED"

class FulfillmentOrderStatus(enum):
    CANCELLED = "CANCELLED"
    CLOSED = "CLOSED"
    IN_PROGRESS = "IN_PROGRESS"
    INCOMPLETE = "INCOMPLETE"
    ON_HOLD = "ON_HOLD"
    OPEN = "OPEN"
    SCHEDULED = "SCHEDULED"

class ProductVariantInventoryPolicy(enum):
    CONTINUE = "CONTINUE"
    DENY = "DENY"

class OrderSortKeys(enum):
    CREATED_AT = "CREATED_AT"
    ID = "ID"
    PROCESSED_AT = "PROCESSED_AT"
    TOTAL_PRICE = "TOTAL_PRICE"
    UPDATED_AT = "UPDATED_AT"


class WeightUnit(enum):
    GRAMS = "GRAMS"
    KILOGRAMS = "KILOGRAMS"
    OUNCES = "OUNCES"
    POUNDS = "POUNDS"

class OrderCancelReason(enum):
    CUSTOMER = "CUSTOMER"
    DECLINED = "DECLINED"
    FRAUD = "FRAUD"
    INVENTORY = "INVENTORY"
    OTHER = "OTHER"


class ProductVariantSortKeys(enum):
    ID = "ID"
    NAME = "NAME"
    POSITION = "POSITION"
    RELEVANCE = "RELEVANCE"
    SKU = "SKU"
    INVENTORY_TOTAL = "INVENTORY_TOTAL"


class ProductStatus(enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DRAFT = "DRAFT"


class CombinedListingsRole(enum):
    NONE = "NONE"
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"


class ProductBundleComponentOptionSelectionStatus(enum):
    DESELECTED = "DESELECTED"
    NEW = "NEW"
    SELECTED = "SELECTED"
    UNAVAILABLE = "UNAVAILABLE"


class CountryCode(enum):
    US = "US"
    CA = "CA"
    GB = "GB"
    AU = "AU"
    FR = "FR"
    DE = "DE"
    IT = "IT"
    ES = "ES"
    NL = "NL"
    JP = "JP"
    CN = "CN"
    IN = "IN"
    BR = "BR"
    MX = "MX"


class LocationSortKeys(enum):
    NAME = "NAME"
    ID = "ID"
    CREATED_AT = "CREATED_AT"
