from .core import Query
from .core.types import (
    Order,
    OrderConnection,
    OrderIdentifierInput,
    OrderSortKeys,
    ProductVariantConnection,
    ProductVariantSortKeys,
)
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
        self.sortKey: OrderSortKeys = sortKey
        self.reverse: bool = reverse
        self.query: Optional[str] = query
        self.after: Optional[str] = after
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}
        self._connection_arguments = connection_arguments or dict(self.__class__._connection_arguments)
