from enum import Enum as PyEnum
from typing import Any, Dict, Type

from pydantic import BaseModel


class TypeRegistry:
    def __init__(self) -> None:
        self._types: Dict[str, Type[Any]] = {}

    def register(self, cls: Type[Any]) -> Type[Any]:
        """Register a Pydantic model or enum class by name for forward-ref resolution."""
        if isinstance(cls, type) and (issubclass(cls, BaseModel) or issubclass(cls, PyEnum)):
            self._types[cls.__name__] = cls
        return cls

    @property
    def types(self) -> Dict[str, Type[Any]]:
        # Return a shallow copy to avoid accidental external mutation.
        return dict(self._types)

    def rebuild_all(self) -> None:
        """Attempt to resolve forward refs across all registered models."""
        namespace = self.types
        for cls in self._types.values():
            if hasattr(cls, "model_rebuild"):
                try:
                    cls.model_rebuild(_types_namespace=namespace)
                except Exception:
                    # Best-effort; individual models may fail if incomplete.
                    continue



type_registry = TypeRegistry()
