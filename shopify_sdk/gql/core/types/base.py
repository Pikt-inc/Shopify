from typing import Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

from .registry import type_registry


class enum(str, Enum):
    pass


class AutoRegisterModel(BaseModel):
    """Base model that auto-registers for forward-ref resolution."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        type_registry.register(cls)


class connection(AutoRegisterModel):
    edges: list[Any]
    nodes: list[Any]

    @property
    def count(self) -> int:
        return len(self.edges)
    
    @property
    def first(self) -> "Any | None":
        return self.nodes[0] if self.nodes else None
    
    @property
    def second(self) -> "Any | None":
        return self.nodes[1] if len(self.nodes) > 1 else None
    
    @property
    def third(self) -> "Any | None":
        return self.nodes[2] if len(self.nodes) > 2 else None
    
    @property
    def last(self) -> "Any | None":
        return self.nodes[-1] if self.nodes else None


Boolean = Optional[bool]
ID = Optional[str]
UnsignedInt64 = Optional[int]
String = Optional[str]
Int = Optional[int]
Float = Optional[float]
URL = Optional[str]
DateTime = Optional[datetime]


class edge(AutoRegisterModel):
    cursor: String
    node: Any
