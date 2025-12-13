from typing import Dict, Type
from pydantic import BaseModel


class TypeRegistry:
    def __init__(self) -> None:
        self._types: Dict[str, Type[BaseModel]] = {}

    def register(self, cls: Type[BaseModel]) -> Type[BaseModel]:
        """Register a Pydantic model class by name for forward-ref resolution."""
        if isinstance(cls, type) and issubclass(cls, BaseModel):
            self._types[cls.__name__] = cls
        return cls

    @property
    def types(self) -> Dict[str, Type[BaseModel]]:
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
