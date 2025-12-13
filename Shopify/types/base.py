from typing import Optional
from datetime import datetime
from enum import Enum

class enum(str, Enum):
    pass

Boolean = Optional[bool]
ID = Optional[str]
UnsignedInt64 = Optional[int]
String = Optional[str]
Int = Optional[int]
URL = Optional[str]
DateTime = Optional[datetime]

