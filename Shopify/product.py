
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from .core import ShopifyResource

class Metafield(BaseModel):
    namespace: str
    key: str
    value: str
    type: str

class Image(ShopifyResource):
    url: str
    altText: Optional[str]

class SelectedOption(ShopifyResource):
    name: str
    value: str

class ProductVariant(ShopifyResource):
    title: str
    sku: Optional[str]
    barcode: Optional[str]
    price: Optional[str]
    compareAtPrice: Optional[str]
    inventoryQuantity: Optional[int]
    inventoryPolicy: Optional[str]
    requiresShipping: Optional[bool]
    weight: Optional[float]
    weightUnit: Optional[str]
    selectedOptions: List[SelectedOption]
    image: Optional[Image]
    createdAt: datetime
    updatedAt: datetime
    metafields: Optional[List[Metafield]]

class ProductOption(ShopifyResource):
    name: str
    values: List[str]

class Product(ShopifyResource):
    title: str
    handle: str
    descriptionHtml: Optional[str]
    vendor: Optional[str]
    productType: Optional[str]
    status: Optional[str]
    tags: List[str]
    createdAt: datetime
    updatedAt: datetime
    publishedAt: Optional[datetime]
    options: List[ProductOption]
    variants: List[ProductVariant]
    images: List[Image]
    metafields: Optional[List[Metafield]]

class Money(BaseModel):
    amount: str
    currencyCode: str

class DiscountAllocation(BaseModel):
    discountedAmount: Money

class OrderLineItem(ShopifyResource):
    title: str
    quantity: int
    sku: Optional[str]
    variantId: Optional[str]
    price: Money
    discountAllocations: List[DiscountAllocation]

class Address(ShopifyResource):
    address1: Optional[str]
    address2: Optional[str]
    city: Optional[str]
    company: Optional[str]
    country: Optional[str]
    countryCode: Optional[str]
    firstName: Optional[str]
    lastName: Optional[str]
    phone: Optional[str]
    province: Optional[str]
    zip: Optional[str]
    default: Optional[bool]

class Customer(ShopifyResource):
    email: Optional[str]
    firstName: Optional[str]
    lastName: Optional[str]
    phone: Optional[str]
    tags: List[str]
    createdAt: datetime
    updatedAt: datetime
    state: Optional[str]
    addresses: List[Address]
    defaultAddress: Optional[Address]
    metafields: Optional[List[Metafield]]






class Order(ShopifyResource):
    name: str
    email: Optional[str]
    createdAt: datetime
    updatedAt: datetime
    totalPrice: Money
    subtotalPrice: Money
    totalTax: Money
    currencyCode: str
    lineItems: List[OrderLineItem]
    customer: Optional[Customer]
    shippingAddress: Optional[Address]
    billingAddress: Optional[Address]
    tags: List[str]
    metafields: Optional[List[Metafield]]

    @property
    def hydrate(self):

class Mutation:
    pass

class Query:
    pass


class OrderIdentifierInput(input_object):
    id: ID. # The ID of the order.

class orderByIdentifier(Query):

    def __init__(
        self,
        identifier: OrderIdentifierInput,
    ) -> Order:
        self.identifier = identifier

    @property
    def body(self) -> str:
        return f'''
        query {{
            orderByIdentifier(identifier: {{id: "{self.identifier.id}"}}) {{
            }}
        }}
        '''
    
    def execute(self, client) -> Order:
        response = client.request(query=self.body)
        print(response)
        order_data = response.get('orderByIdentifier', {})
        return Order(**order_data)