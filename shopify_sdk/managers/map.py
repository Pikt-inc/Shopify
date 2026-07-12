from __future__ import annotations

from collections.abc import Callable, Iterable
from importlib import import_module
from typing import Any, ClassVar, Optional, Type, get_args, cast

from pydantic import BaseModel

from shopify_sdk.gql.core.query import Query
from shopify_sdk.gql.core.types.connections import connection


QueryFactory = Callable[..., Query]


class MapManagerException(Exception):
    """Custom exception for MapManager errors."""

    pass


class MapManager(BaseModel):
    """
    Purpose of this class is to offer a clean interface for building 'lookup' maps of products.
    ie. handle -> id, sku -> id, sku -> price, etc.
    Main support is only for fields directly on the object, but nested fields can be supported via dot notation.
    You can use the inclusion_overrides parameter to specify additional fields to include in the query.
    Example usage:
        store.map.get(ProductVariant, 'product.id', 'price', {'ProductVariant': {'id', 'price', 'product'}, 'Product': {'id'}})

    :var synchronous: Description
    :vartype synchronous: tuple[Literal[False], Any]
    :var Args: Description
    """

    _MODEL_QUERY_NAMES: ClassVar[dict[str, str]] = {
        "DeliveryProfile": "deliveryProfiles",
        "Location": "locations",
        "Order": "orders",
        "Product": "products",
        "ProductVariant": "productVariants",
        "Publication": "publications",
    }

    # @validate_call(validate_return=True)
    def get(
        self,
        model: Type[BaseModel],
        field_key: str,
        value_key: str,
        inclusion_overrides: Optional[dict[str, set[str]]] = None,
    ) -> dict[str, str]:
        """Return a lookup map from one model field path to another.

        :param model: GraphQL object model to query.
        :param field_key: Source field path used as the dictionary key.
        :param value_key: Destination field path used as the dictionary value.
        :param inclusion_overrides: Optional field inclusions for nested lookups.
        :returns: Mapping of source field values to destination field values.
        """
        query_factory = self._require_query_factory(model)
        connection_instance = self._build_and_execute_query(
            query_factory, model, field_key, value_key, inclusion_overrides
        )
        return self._connection_to_map(
            cast(connection, connection_instance), field_key, value_key
        )

    def _require_query_factory(self, model: Type[BaseModel]) -> QueryFactory:
        """Return the query factory for a model or raise a map-specific error.

        :param model: GraphQL object model to query.
        :returns: Query class or versioned query proxy for the model.
        """
        query_factory = self._get_query_class(model)
        if query_factory:
            return query_factory
        raise MapManagerException(f"No query class found for model: {model.__name__}")

    def _connection_to_map(
        self, connection_instance: connection, field_key: str, value_key: str
    ) -> dict[str, str]:
        """Convert connection nodes into a string lookup map.

        :param connection_instance: Bulk query connection response.
        :param field_key: Source field path used as the dictionary key.
        :param value_key: Destination field path used as the dictionary value.
        :returns: Mapping of source field values to destination field values.
        """
        if not connection_instance.nodes or connection_instance.count == 0:
            return {}
        result_map: dict[str, str] = {}
        for node in connection_instance.nodes:
            field_value = self.getattr_nested(node, field_key, None)
            value_value = self.getattr_nested(node, value_key, None)
            if field_value is not None and value_value is not None:
                result_map[str(field_value)] = str(value_value)
        return result_map

    def getattr_nested(self, obj: object, path: str, default: Any = None) -> Any:
        """Return a dotted-path value from an object or nested dictionaries.

        :param obj: Object or dictionary to inspect.
        :param path: Dot-delimited attribute path.
        :param default: Value returned when any path segment is missing.
        :returns: The nested value or the default.
        """
        current = obj
        for part in path.split("."):
            if current is None:
                return default
            try:
                current = getattr(current, part)
            except AttributeError:
                if isinstance(current, dict):
                    return current.get(part, default)
                return default
        return current

    # @validate_call(validate_return=True)
    def _build_and_execute_query(
        self,
        query_factory: QueryFactory,
        model: Type[BaseModel],
        field_key: str,
        value_key: str,
        inclusion_overrides: Optional[dict[str, set[str]]] = None,
    ) -> BaseModel:
        """Build and execute a bulk query for the requested model fields.

        :param query_factory: Query class or versioned query proxy.
        :param model: GraphQL object model to query.
        :param field_key: Source field path used as the dictionary key.
        :param value_key: Destination field path used as the dictionary value.
        :param inclusion_overrides: Optional explicit field inclusions.
        :returns: Bulk query connection response.
        """
        if not inclusion_overrides:
            field_inclusions = {model.__name__: {field_key, value_key}}
        else:
            field_inclusions = inclusion_overrides
        built_query = query_factory(field_inclusions=field_inclusions)
        return built_query.bulk()

    def _get_query_class(
        self,
        model: Type[BaseModel],
    ) -> Optional[QueryFactory]:
        """Return a query factory for the model without requiring caller changes.

        :param model: GraphQL object model to query.
        :returns: Query class or versioned query proxy for the model.
        """
        return self._registered_query_factory(model) or self._legacy_query_class(model)

    def _registered_query_factory(
        self, model: Type[BaseModel]
    ) -> Optional[QueryFactory]:
        """Resolve known Shopify models through the versioned query registry.

        :param model: GraphQL object model to query.
        :returns: Version-aware query proxy when the model is known.
        """
        query_name = self._MODEL_QUERY_NAMES.get(model.__name__)
        if query_name is None:
            return None
        query_module = import_module("shopify_sdk.gql.queries")
        query_factory = getattr(query_module, query_name, None)
        return cast(Optional[QueryFactory], query_factory)

    def _legacy_query_class(self, model: Type[BaseModel]) -> Optional[Type[Query]]:
        """Fall back to historical subclass discovery for custom query classes.

        :param model: GraphQL object model to query.
        :returns: Query class discovered from loaded subclasses, when available.
        """
        for conn_class in self._connection_subclasses():
            node_type = self._get_node_type(conn_class)
            if isinstance(node_type, type) and issubclass(node_type, model):
                for query_class in self._query_subclasses():
                    if (
                        query_class.return_type
                        and query_class.return_type == conn_class
                    ):
                        return query_class
        return None

    def _connection_subclasses(self) -> Iterable[Type[connection]]:
        """Yield loaded connection subclasses recursively."""
        yield from self._subclasses(connection)

    def _query_subclasses(self) -> Iterable[Type[Query]]:
        """Yield loaded query subclasses recursively."""
        yield from self._subclasses(Query)

    def _subclasses(self, cls: Type[Any]) -> Iterable[Type[Any]]:
        """Yield all loaded subclasses of a class recursively.

        :param cls: Parent class to inspect.
        :returns: Iterator of subclasses at any depth.
        """
        for subclass in cls.__subclasses__():
            yield subclass
            yield from self._subclasses(subclass)

    def _get_node_type(
        self,
        connection_class: Type[connection],
    ) -> Optional[Type[BaseModel]]:
        """Retrieve the node type from a connection class.

        :param connection_class: Connection model class to inspect.
        :returns: Node model type when available.
        """
        fields = connection_class.__pydantic_fields__
        if "nodes" not in fields.keys():
            return None
        nodes_field_info = fields["nodes"]
        annotation = nodes_field_info.annotation
        args = get_args(annotation)
        node_type = args[0] if args else None
        return node_type


# original
# from shopify_sdk import store
# from shopify_sdk.gql.core.types.objects import ProductVariant
# store.map.get(ProductVariant, 'product.id', 'price', {'ProductVariant': {'id', 'price', 'product'}, 'Product': {'id'}})

# # to this
# from shopify_sdk import store
# from shopify_sdk.gql.core.types.objects import Product, ProductVariant
# store.map.get(ProductVariant, ProductVariant.id, ProductVariant.product.id)
