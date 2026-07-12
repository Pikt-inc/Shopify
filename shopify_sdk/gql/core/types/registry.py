from enum import Enum as PyEnum
from collections import defaultdict
from typing import Any, Dict, Iterable, Type

from pydantic import BaseModel


class TypeRegistry:
    def __init__(self) -> None:
        self._types: Dict[str, Type[Any]] = {}
        self._qualified_types: Dict[str, Type[Any]] = {}

    def register(self, cls: Type[Any]) -> Type[Any]:
        """Register a Pydantic model or enum class by name for forward-ref resolution."""
        if isinstance(cls, type) and (
            issubclass(cls, BaseModel) or issubclass(cls, PyEnum)
        ):
            self._types[cls.__name__] = cls
            self._qualified_types[f"{cls.__module__}.{cls.__name__}"] = cls
        return cls

    @property
    def types(self) -> Dict[str, Type[Any]]:
        # Return a shallow copy to avoid accidental external mutation.
        return dict(self._types)

    def namespace_for_module(self, module_name: str) -> Dict[str, Type[Any]]:
        """Return registered classes that belong to a module's type package.

        :param module_name: Module path for a model or type package.
        :returns: Name-to-class namespace scoped to that type package.
        """
        prefix = self._type_package_prefix(module_name)
        return {
            cls.__name__: cls
            for cls in self._qualified_types.values()
            if cls.__module__.startswith(prefix)
        }

    def rebuild_all(self) -> None:
        """Attempt to resolve forward refs across all registered models."""
        for prefix, classes in self._classes_by_type_package().items():
            namespace = self.namespace_for_module(prefix)
            for cls in classes:
                if hasattr(cls, "model_rebuild"):
                    try:
                        cls.model_rebuild(_types_namespace=namespace)
                    except Exception:
                        # Best-effort; individual models may fail if incomplete.
                        continue

    def _classes_by_type_package(self) -> Dict[str, list[Type[Any]]]:
        """Group registered classes by their owning type package."""
        grouped: Dict[str, list[Type[Any]]] = defaultdict(list)
        for cls in self._qualified_types.values():
            grouped[self._type_package_prefix(cls.__module__)].append(cls)
        return grouped

    def _type_package_prefix(self, module_name: str) -> str:
        """Return the package prefix used to resolve related GraphQL types."""
        marker = ".types"
        if marker not in module_name:
            return module_name
        return f"{module_name.split(marker, 1)[0]}{marker}"

    def rebuild(self, classes: Iterable[Type[Any]], module_name: str) -> None:
        """Attempt to resolve forward refs for classes in one type package.

        :param classes: Classes to rebuild.
        :param module_name: Module path whose type package provides the namespace.
        """
        namespace = self.namespace_for_module(module_name)
        for cls in classes:
            if hasattr(cls, "model_rebuild"):
                try:
                    cls.model_rebuild(_types_namespace=namespace)
                except Exception:
                    # Best-effort; individual models may fail if incomplete.
                    continue


type_registry = TypeRegistry()
