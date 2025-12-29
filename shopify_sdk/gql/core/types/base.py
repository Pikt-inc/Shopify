from typing import Any, TYPE_CHECKING, Iterable, Set
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

if TYPE_CHECKING:
    from .enums import WeightUnit

from .registry import type_registry


class enum(str, Enum):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        type_registry.register(cls)


class AutoRegisterModel(BaseModel):
    """Base model that auto-registers for forward-ref resolution."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        type_registry.register(cls)

    @classmethod
    def fields_except(
        cls, exclude: Iterable[str] = (), ordered: bool = False
    ) -> "Set[str]":
        """Return the model's field names excluding those in `exclude`.

        - `exclude` may be any iterable of field names to remove.
        - If `ordered` is True, returns a list preserving the declaration order
          (uses `model_fields` when available, otherwise `__annotations__`).
        - If `ordered` is False, returns a set of remaining field names.
        """
        exclude_set = set(exclude or ())
        model_fields = getattr(cls, "model_fields", None)
        if model_fields:
            names = list(model_fields.keys())
        else:
            names = list(getattr(cls, "__annotations__", {}).keys())

        if ordered:
            return set([n for n in names if n not in exclude_set])
        return set(names) - exclude_set


class connection(AutoRegisterModel):
    edges: list[Any]
    nodes: list[Any]

    @property
    def validated_nodes(self) -> list[Any]:
        if len(self.nodes) != 0:
            return self.nodes
        return [edge.node for edge in self.edges]

    @property
    def count(self) -> int:
        return len(self.validated_nodes)

    @property
    def first(self) -> "Any | None":
        return self.validated_nodes[0] if self.validated_nodes else None

    @property
    def second(self) -> "Any | None":
        return self.validated_nodes[1] if len(self.validated_nodes) > 1 else None

    @property
    def third(self) -> "Any | None":
        return self.validated_nodes[2] if len(self.validated_nodes) > 2 else None

    @property
    def last(self) -> "Any | None":
        return self.validated_nodes[-1] if self.validated_nodes else None


Boolean = bool
ID = str
UnsignedInt64 = int
String = str
Int = int
Float = float
URL = str
DateTime = datetime
Money = String  # Scalar


class edge(AutoRegisterModel):
    cursor: String
    node: Any


class Weight(AutoRegisterModel):
    unit: "WeightUnit"
    value: Float
