from .core import Query
from .core.types.enums import *
from .core.types.input_objects import *
from .core.types.objects import *
from .core.types.connections import *

from typing import Type, Optional, Dict, Set, Any
from shopify_sdk.gql.core.client import ShopifyClient


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
        self._connection_arguments = connection_arguments or dict(
            self.__class__._connection_arguments
        )

    def execute(self, client: ShopifyClient) -> Optional[Order]:
        result: Optional[Order] = super().execute(client=client)
        return result


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
        self._connection_arguments = connection_arguments or dict(
            self.__class__._connection_arguments
        )

    def execute(self, client: ShopifyClient) -> OrderConnection:
        result: OrderConnection = super().execute(client=client)
        return result


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
        self._connection_arguments = connection_arguments or dict(
            self.__class__._connection_arguments
        )

    def execute(self, client: ShopifyClient) -> ProductVariantConnection:
        result: ProductVariantConnection = super().execute(client=client)
        return result


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
        self._connection_arguments = connection_arguments or dict(
            self.__class__._connection_arguments
        )

    def execute(self, client: ShopifyClient) -> ProductConnection:
        result: ProductConnection = super().execute(client=client)
        return result


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
        self._connection_arguments = connection_arguments or dict(
            self.__class__._connection_arguments
        )

    def execute(self, client: ShopifyClient) -> PublicationConnection:
        result: PublicationConnection = super().execute(client=client)
        return result


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
        self._connection_arguments = connection_arguments or dict(
            self.__class__._connection_arguments
        )

    def execute(self, client: ShopifyClient) -> Optional[Product]:
        result: Optional[Product] = super().execute(client=client)
        return result


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
        self._connection_arguments = connection_arguments or dict(
            self.__class__._connection_arguments
        )

    def execute(self, client: ShopifyClient) -> LocationConnection:
        result: LocationConnection = super().execute(client=client)
        return result


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
        self._connection_arguments = connection_arguments or dict(
            self.__class__._connection_arguments
        )

    @property
    def fields(self) -> str:
        spacer = " " * (self._indent * 2)
        inner_indent = self._indent * 3
        selection = self._build_model_selection(self.return_type, indent=inner_indent)
        if not selection.strip():
            selection = f"{' ' * inner_indent}__typename"
        return "\n".join(
            [
                f"{spacer}... on {self.return_type.__name__} {{",
                selection,
                f"{spacer}}}",
            ]
        )

    def execute(self, client: ShopifyClient) -> Optional[BulkOperation]:
        result: Optional[BulkOperation] = super().execute(client=client)
        return result


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
        default_inclusions = {
            "ProductSetOperation": {"id", "status", "product", "userErrors"},
            "Product": {"id"},
        }
        self._field_inclusions = (
            default_inclusions if field_inclusions is None else field_inclusions
        )
        self._connection_arguments = connection_arguments or dict(
            self.__class__._connection_arguments
        )

    def execute(self, client: ShopifyClient) -> Optional[ProductSetOperation]:
        result: Optional[ProductSetOperation] = super().execute(client=client)
        return result


class deliveryProfiles(Query):
    return_type: Type[BaseModel] = DeliveryProfileConnection

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
        self._connection_arguments = connection_arguments or dict(
            self.__class__._connection_arguments
        )

    def execute(self, client: ShopifyClient) -> Optional[DeliveryProfileConnection]:
        result: Optional[DeliveryProfileConnection] = super().execute(client=client)
        return result