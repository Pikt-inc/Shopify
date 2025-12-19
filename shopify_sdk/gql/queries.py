from .core import Query
from .core.types.enums import *
from .core.types.input_objects import *
from .core.types.objects import *
from .core.types.connections import *

from typing import Type, Optional, Dict, Set, Any
from pydantic import BaseModel

class orderByIdentifier(Query):
    return_type: Type[BaseModel] = Order

    def __init__(
        self,
        identifier: OrderIdentifierInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
        connection_arguments: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.identifier: OrderIdentifierInput = identifier
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}
        self._connection_arguments = connection_arguments or dict(self.__class__._connection_arguments)


class orders(Query):
    return_type: Type[BaseModel] = OrderConnection

    def __init__(
        self,
        first: int = 1,
        sortKey: OrderSortKeys = OrderSortKeys.PROCESSED_AT,
        reverse: bool = True,
        query: Optional[str] = None,
        after: Optional[str] = None,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
        connection_arguments: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.first: int = first
        self.sortKey: OrderSortKeys = sortKey
        self.reverse: bool = reverse
        self.query: Optional[str] = query
        self.after: Optional[str] = after
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}
        self._connection_arguments = connection_arguments or dict(self.__class__._connection_arguments)


class productVariants(Query):
    return_type: Type[BaseModel] = ProductVariantConnection

    def __init__(
        self,
        first: int = 1,
        sortKey: Optional[ProductVariantSortKeys] = None,
        reverse: bool = True,
        query: Optional[str] = None,
        after: Optional[str] = None,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
        connection_arguments: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.first: int = first
        self.sortKey: Optional[ProductVariantSortKeys] = sortKey
        self.reverse: bool = reverse
        self.query: Optional[str] = query
        self.after: Optional[str] = after
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}
        self._connection_arguments = connection_arguments or dict(self.__class__._connection_arguments)


class products(Query):
    return_type: Type[BaseModel] = ProductConnection

    def __init__(
        self,
        first: int = 100,
        sortKey: Optional[ProductSortKeys] = None,
        reverse: bool = False,
        query: Optional[str] = None,
        after: Optional[str] = None,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
        connection_arguments: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.first: int = first
        self.sortKey: Optional[ProductSortKeys] = sortKey
        self.reverse: bool = reverse
        self.query: Optional[str] = query
        self.after: Optional[str] = after
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}
        self._connection_arguments = connection_arguments or dict(self.__class__._connection_arguments)


class publications(Query):
    return_type: Type[BaseModel] = PublicationConnection

    def __init__(
        self,
        first: int = 20,
        after: Optional[str] = None,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
        connection_arguments: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.first: int = first
        self.after: Optional[str] = after
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}
        self._connection_arguments = connection_arguments or dict(self.__class__._connection_arguments)


class productByIdentifier(Query):
    return_type: Type[BaseModel] = Product

    def __init__(
        self,
        identifier: ProductIdentifierInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
        connection_arguments: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.identifier: ProductIdentifierInput = identifier
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}
        self._connection_arguments = connection_arguments or dict(self.__class__._connection_arguments)


class locations(Query):
    return_type: Type[BaseModel] = LocationConnection

    def __init__(
        self,
        first: int = 20,
        after: Optional[str] = None,
        before: Optional[str] = None,
        last: Optional[int] = None,
        includeInactive: bool = False,
        includeLegacy: bool = False,
        query: Optional[str] = None,
        reverse: bool = False,
        sortKey: LocationSortKeys = LocationSortKeys.NAME,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
        connection_arguments: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.first: int = first
        self.after: Optional[str] = after
        self.before: Optional[str] = before
        self.last: Optional[int] = last
        self.includeInactive: bool = includeInactive
        self.includeLegacy: bool = includeLegacy
        self.query: Optional[str] = query
        self.reverse: bool = reverse
        self.sortKey: LocationSortKeys = sortKey
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}
        self._connection_arguments = connection_arguments or dict(self.__class__._connection_arguments)


class bulkOperation(Query):
    return_type: Type[BaseModel] = BulkOperation

    @property
    def class_name(self) -> str:
        # Some Shopify API versions expose BulkOperation via `node(id:)` rather than a
        # dedicated `bulkOperation(id:)` field on QueryRoot. Using `node` keeps polling
        # compatible across versions.
        return "node"

    def __init__(
        self,
        id: ID,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
        connection_arguments: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.id: ID = id
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}
        self._connection_arguments = connection_arguments or dict(self.__class__._connection_arguments)

    @property
    def fields(self) -> str:
        spacer = " " * (self._indent * 2)
        inner = " " * (self._indent * 3)
        bulk_block = "\n".join(
            [
                f"{spacer}... on BulkOperation {{",
                f"{inner}id",
                f"{inner}status",
                f"{inner}objectCount",
                f"{inner}errorCode",
                f"{inner}url",
                f"{inner}partialDataUrl",
                f"{spacer}}}",
            ]
        )
        return bulk_block


class productSetOperation(Query):
    return_type: Type[BaseModel] = ProductSetOperation

    def __init__(
        self,
        id: ID,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
        connection_arguments: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.id: ID = id
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {
            "ProductSetOperation": {"id", "status", "product", "userErrors"},
            "Product": {"id"},
        }
        self._connection_arguments = connection_arguments or dict(self.__class__._connection_arguments)

    @property
    def fields(self) -> str:
        spacer = " " * (self._indent * 2)
        inner = " " * (self._indent * 3)
        product_block = "\n".join(
            [
                f"{spacer}product {{",
                f"{inner}id",
                f"{spacer}}}",
            ]
        )
        user_errors_block = "\n".join(
            [
                f"{spacer}userErrors {{",
                f"{inner}code",
                f"{inner}message",
                f"{inner}field",
                f"{spacer}}}",
            ]
        )
        return "\n".join(
            [
                f"{spacer}id",
                f"{spacer}status",
                product_block,
                user_errors_block,
            ]
        )
