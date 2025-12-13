import sys
from enum import Enum
from typing import Optional, Dict, Any, Type, List, Tuple, Union, Set, get_args, get_origin, get_type_hints, cast

from pydantic import BaseModel

from .types import type_registry
from .types.base import connection
from .client import ShopifyClient

class Query:
    return_type: Optional[Type[BaseModel]] = None
    _connection_arguments: Dict[str, Dict[str, Any]] = {}
    _field_exclusions: Dict[str, Set[str]] = {}
    _field_inclusions: Dict[str, Set[str]] = {}
    _indent: int = 2
    default_connection_first: Optional[int] = 100

    def __init__(
        self
    ):
        pass

    @property
    def connection_arguments(self) -> Dict[str, Dict[str, Any]]:
        # class-level default allows subclasses to override without polluting __dict__
        return getattr(self, "_connection_arguments", self.__class__._connection_arguments)

    @property
    def field_exclusions(self) -> Dict[str, Set[str]]:
        # class-level default allows subclasses to override without polluting __dict__
        return getattr(self, "_field_exclusions", self.__class__._field_exclusions)

    @property
    def field_inclusions(self) -> Dict[str, Set[str]]:
        # class-level default allows subclasses to override without polluting __dict__
        return getattr(self, "_field_inclusions", self.__class__._field_inclusions)

    @property
    def class_name(self):
        return self.__class__.__name__ 

    @property
    def arguments(self):
        inputs = self._input_arguments
        annotations = self._get_argument_annotations()

        parts = []
        for name, value in inputs.items():
            gql_type, nullable = self._graphql_type_for_argument(
                annotation=annotations.get(name),
                value=value,
            )
            required_marker = "" if nullable else "!"
            parts.append(f"${name}: {gql_type}{required_marker}")

        return ", ".join(parts)

    @property
    def _input_arguments(self) -> Dict[str, Any]:
        # filters out internal/private attributes (e.g., _connection_arguments)
        return {
            name: value
            for name, value in self.__dict__.items()
            if not name.startswith("_")
        }
    
    @property
    def fields(self):
        if self.return_type is None:
            raise ValueError("return_type must be defined to access fields.")
        return self._build_model_selection(self.return_type, indent=self._indent * 2)

    def _build_model_selection(self, model: Type[BaseModel], indent: int) -> str:
        type_hints = self._get_type_hints(model)
        model_fields = getattr(model, "model_fields", {}) or {}
        field_names = list(model_fields.keys() or type_hints.keys())
        lines = []
        for name in field_names:
            if type_hints.get(name) is None or not self._should_include_field(model, name):
                continue
            field_info = model_fields.get(name)
            alias = getattr(field_info, "alias", None) if field_info else None
            lines.append(self._build_field_selection(name, type_hints.get(name), indent, alias))
        return "\n".join(lines)

    def _build_field_selection(self, name: str, annotation: Any, indent: int, graphql_name: str | None = None) -> str:
        resolved = self._unwrap_annotation(annotation)
        spacer = " " * indent
        field_label = graphql_name or name

        if self._is_connection(resolved):
            return self._build_connection_selection(name, resolved, indent, graphql_name=field_label)

        if self._is_model(resolved):
            nested = self._build_model_selection(resolved, indent + self._indent)
            return f"{spacer}{field_label} {{\n{nested}\n{spacer}}}"

        return f"{spacer}{field_label}"

    def _build_connection_selection(self, name: str, conn_type: Type[BaseModel], indent: int, graphql_name: str | None = None) -> str:
        spacer = " " * indent
        inner_indent = indent + self._indent
        conn_hints = self._get_type_hints(conn_type)
        field_label = graphql_name or name

        sections = []

        edges_type = self._unwrap_annotation(conn_hints.get("edges"))
        if self._is_model(edges_type):
            edges_body = self._build_model_selection(edges_type, inner_indent + self._indent)
            sections.append(f"{' ' * inner_indent}edges {{\n{edges_body}\n{' ' * inner_indent}}}")

        nodes_type = self._unwrap_annotation(conn_hints.get("nodes"))
        if self._is_model(nodes_type):
            nodes_body = self._build_model_selection(nodes_type, inner_indent + self._indent)
            sections.append(f"{' ' * inner_indent}nodes {{\n{nodes_body}\n{' ' * inner_indent}}}")

        page_info_type = self._unwrap_annotation(conn_hints.get("pageInfo"))
        if self._is_model(page_info_type):
            page_info_body = self._build_model_selection(page_info_type, inner_indent + self._indent)
            sections.append(f"{' ' * inner_indent}pageInfo {{\n{page_info_body}\n{' ' * inner_indent}}}")

        args_fragment = self._format_connection_args(name, conn_type)
        if not sections:
            return f"{spacer}{field_label}{args_fragment}"

        section_body = "\n".join(sections)
        return f"{spacer}{field_label}{args_fragment} {{\n{section_body}\n{spacer}}}"

    def _format_connection_args(self, field_name: str, conn_type: Type[BaseModel]) -> str:
        args = self.connection_arguments.get(field_name)
        if not args:
            if self.default_connection_first is None:
                return ""
            args = {"first": self.default_connection_first}
        formatted = ", ".join(f"{key}: {self._format_literal(value)}" for key, value in args.items())
        return f"({formatted})"

    def _format_literal(self, value: Any) -> str:
        if isinstance(value, str):
            return f'"{value}"'
        if isinstance(value, bool):
            return str(value).lower()
        if value is None:
            return "null"
        return str(value)

    def _unwrap_annotation(self, annotation: Any) -> Any:
        if annotation is None:
            return None
        origin = get_origin(annotation)
        if origin is None:
            return annotation
        if origin is list or origin is List:
            list_args = get_args(annotation)
            return self._unwrap_annotation(list_args[0]) if list_args else Any
        if origin is Union:
            union_args = [arg for arg in get_args(annotation) if arg is not type(None)]
            return self._unwrap_annotation(union_args[0]) if union_args else Any
        return annotation

    def _is_model(self, annotation: Any) -> bool:
        return isinstance(annotation, type) and issubclass(annotation, BaseModel)

    def _is_connection(self, annotation: Any) -> bool:
        return isinstance(annotation, type) and issubclass(annotation, connection)

    def _is_field_excluded(self, model: Type[BaseModel], field_name: str) -> bool:
        exclusions = self.field_exclusions.get(model.__name__)
        return exclusions is not None and field_name in exclusions

    def _is_field_included(self, model: Type[BaseModel], field_name: str) -> bool:
        inclusions = self.field_inclusions.get(model.__name__)
        if inclusions is None:
            return True
        return field_name in inclusions

    def _should_include_field(self, model: Type[BaseModel], field_name: str) -> bool:
        if self._is_field_excluded(model, field_name):
            return False
        return self._is_field_included(model, field_name)

    def _build_partial_model(self, data: Any, model: Type[BaseModel]) -> BaseModel:
        """Construct a model instance without requiring excluded/missing fields."""
        type_hints = self._get_type_hints(model)
        payload: Dict[str, Any] = {}
        data_dict = data if isinstance(data, dict) else {}
        model_fields = getattr(model, "model_fields", {}) or {}

        for field_name, annotation in type_hints.items():
            annotation = type_hints.get(field_name)

            if not self._should_include_field(model, field_name):
                payload[field_name] = self._default_value_for(annotation)
                continue

            field_info = model_fields.get(field_name)
            alias = getattr(field_info, "alias", None) if field_info else None
            data_key = alias if alias in data_dict else field_name

            if data_key not in data_dict:
                payload[field_name] = self._default_value_for(annotation)
                continue

            payload[field_name] = self._build_partial_value(
                value=data_dict[data_key],
                annotation=annotation,
            )

        return model.model_construct(**payload)

    def _build_partial_value(self, value: Any, annotation: Any) -> Any:
        resolved = self._unwrap_annotation(annotation)
        origin = get_origin(annotation)

        if origin is list or origin is List:
            list_args = get_args(annotation)
            inner = self._unwrap_annotation(list_args[0]) if list_args else Any
            if self._is_model(inner) or self._is_connection(inner):
                inner_model: Type[BaseModel] = cast(Type[BaseModel], inner)
                return [
                    self._build_partial_model(item, inner_model) if isinstance(item, dict) else item
                    for item in value or []
                ]
            return value

        if self._is_model(resolved) or self._is_connection(resolved):
            model_type: Type[BaseModel] = cast(Type[BaseModel], resolved)
            if isinstance(value, dict):
                return self._build_partial_model(value, model_type)
            return value

        return value

    def _default_value_for(self, annotation: Any) -> Any:
        if annotation is None:
            return None
        origin = get_origin(annotation)
        if origin is list or origin is List:
            return []
        resolved = self._unwrap_annotation(annotation)
        if self._is_connection(resolved):
            try:
                return resolved.model_construct(edges=[], nodes=[], pageInfo=None)
            except Exception:
                return resolved.model_construct()
        if self._is_model(resolved):
            return resolved.model_construct()
        return None

    def _get_type_hints(self, model: Type[BaseModel]) -> Dict[str, Any]:
        try:
            module = sys.modules.get(model.__module__)
            globalns: Dict[str, Any] = type_registry.types
            if module:
                globalns.update(module.__dict__)
            return get_type_hints(model, globalns=globalns, localns=globalns)
        except Exception:
            annotations = getattr(model, "__annotations__", {}) or {}
            resolved = {}
            for key, value in annotations.items():
                if isinstance(value, str) and value in type_registry.types:
                    resolved[key] = type_registry.types[value]
                else:
                    resolved[key] = value
            return resolved

    def _get_argument_annotations(self) -> Dict[str, Any]:
        init_method = self.__class__.__init__
        try:
            module = sys.modules.get(init_method.__module__)
            globalns: Dict[str, Any] = type_registry.types
            if module:
                globalns = {**module.__dict__, **globalns}
            hints = get_type_hints(init_method, globalns=globalns, localns=globalns)
        except Exception:
            hints = getattr(init_method, "__annotations__", {}) or {}

        hints.pop("return", None)
        hints.pop("self", None)
        return hints

    def _graphql_type_for_argument(self, annotation: Any, value: Any) -> Tuple[str, bool]:
        """Return (GraphQL type name, is_nullable)."""
        nullable = False
        resolved = annotation

        if resolved is not None:
            origin = get_origin(resolved)
            if origin is Union:
                union_args = [arg for arg in get_args(resolved) if arg is not type(None)]
                resolved = union_args[0] if union_args else Any
                nullable = True
                origin = get_origin(resolved)

            if origin is list or origin is List:
                inner = get_args(resolved)
                inner_type, _ = self._graphql_type_for_argument(inner[0] if inner else Any, None)
                return f"[{inner_type}]", nullable

            scalar_map = {
                str: "String",
                int: "Int",
                bool: "Boolean",
                float: "Float",
            }
            if resolved in scalar_map:
                return scalar_map[resolved], nullable
            if isinstance(resolved, type):
                return resolved.__name__, nullable

        return self._graphql_type_from_value(value), nullable

    def _graphql_type_from_value(self, value: Any) -> str:
        scalar_map = {
            str: "String",
            int: "Int",
            bool: "Boolean",
            float: "Float",
        }
        if isinstance(value, list) and value:
            inner_type = self._graphql_type_from_value(value[0])
            return f"[{inner_type}]"

        value_type = type(value)
        return scalar_map.get(value_type, value_type.__name__)

    @property
    def body(self) -> str:
        args_list = self._input_arguments
        args_string = ", ".join(f"{name}: ${name}" for name in args_list.keys())

        return "\n".join([
            f"query {self.class_name}({self.arguments}) {{",
            f"{' ' * self._indent}{self.class_name}({args_string}) {{",
            f"{self.fields}",
            f"{' ' * self._indent}}}",
            "}",
        ])
    
    def execute(self, client: ShopifyClient):
        variables: Dict[str, Any] = {}
        for name, value in self._input_arguments.items():
            if value is None:
                variables[name] = None
            elif hasattr(value, "to_graphql"):
                variables[name] = value.to_graphql()
            elif isinstance(value, Enum):
                variables[name] = value.value
            else:
                variables[name] = value

        response = client.request(
            query=self.body,
            variables=variables
        )
        
        if response.data is None:
            raise ValueError("Response data is None.")
        order_data = response.data.get(self.class_name)
        if order_data is None:
            return None
        if not isinstance(order_data, dict):
            raise TypeError(f"Response data for the class must be a dictionary, got {type(order_data).__name__}.")
        if self.return_type is None:
            raise ValueError("return_type must be defined to cast the response.")
        if not isinstance(self.return_type, type):
            raise TypeError("return_type must be a class type derived from BaseModel.")
        # When fields were excluded/included, construct a partial model so missing
        # fields default to None instead of raising validation errors.
        if self.field_exclusions or self.field_inclusions:
            cast_obj = self._build_partial_model(order_data, self.return_type)
        else:
            cast_obj = self.return_type(**order_data)
        return cast_obj
