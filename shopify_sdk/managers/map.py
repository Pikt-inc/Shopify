from __future__ import annotations

from typing import Type, Optional, get_args, cast
from pydantic import BaseModel, validate_call

from shopify_sdk.gql.core.query import Query
from shopify_sdk.gql.core.types.connections import connection


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

    # @validate_call(validate_return=True)
    def get(
        self,
        model: Type[BaseModel],
        field_key: str,
        value_key: str,
        inclusion_overrides: Optional[dict[str, set[str]]] = None,
    ) -> dict[str, str]:
        query_class: Optional[Type[Query]] = self._get_query_class(model)
        if not query_class:
            raise MapManagerException(
                f"No query class found for model: {model.__name__}"
            )

        # Build and execute the query
        connection_instance = self._build_and_execute_query(
            query_class, model, field_key, value_key, inclusion_overrides
        )
        # bulk() returns a pydantic BaseModel that subclasses `connection`.
        # Cast so the static type checker knows `nodes`/`count` exist.
        connection_instance = cast(connection, connection_instance)
        if not connection_instance.nodes or connection_instance.count == 0:
            return {}

        result_map = {}
        for node in connection_instance.nodes:
            field_value = self.getattr_nested(node, field_key, None)
            value_value = self.getattr_nested(node, value_key, None)
            if field_value is not None and value_value is not None:
                result_map[str(field_value)] = str(value_value)
        return result_map

    def getattr_nested(self, obj, path: str, default=None):
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
        query_class: Type[Query],
        model: Type[BaseModel],
        field_key: str,
        value_key: str,
        inclusion_overrides: Optional[dict[str, set[str]]] = None,
    ) -> BaseModel:
        """
        Builds a query to fetch the specified field and value keys.

        :type query: Type[Query]
        :type field_key: str
        :type value_key: str
        :return: The constructed query.
        :rtype: Query
        """
        if not inclusion_overrides:
            field_inclusions = {model.__name__: {field_key, value_key}}
        else:
            field_inclusions = inclusion_overrides
        built_query = query_class(field_inclusions=field_inclusions)
        return built_query.bulk()

    @validate_call(validate_return=True)
    def _get_query_class(
        self,
        model: Type[BaseModel],
    ) -> Optional[Type[Query]]:
        """
        Searches through defined Query classes to find one that returns the specified model.

        :type model: Type[BaseModel]
        :return: Description
        :rtype: Type[Query]
        """
        connection_subclasses = (
            connection.__subclasses__()
        )  # Get all connection subclasses
        query_subclasses = Query.__subclasses__()  # Get all Query subclasses
        for conn_class in connection_subclasses:
            node_type = self._get_node_type(conn_class)
            if node_type and issubclass(node_type, model):
                for query_class in query_subclasses:
                    if (
                        query_class.return_type
                        and query_class.return_type == conn_class
                    ):
                        return query_class
        return None

    def _get_node_type(
        self,
        connection_class: Type[connection],
    ) -> Optional[Type[BaseModel]]:
        """
        Retrieves the node type from a connection class.

        :type connection_class: Type[connection]
        :return: The node type if found, None otherwise.
        :rtype: Type[BaseModel]
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
