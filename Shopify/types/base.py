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
    pass


Boolean = Optional[bool]
ID = Optional[str]
UnsignedInt64 = Optional[int]
String = Optional[str]
Int = Optional[int]
URL = Optional[str]
DateTime = Optional[datetime]


class edge(AutoRegisterModel):
    cursor: String
    node: Any
