from typing import NewType
from datetime import datetime
from typing import Union
from enum import Enum

class enum(str, Enum):
    pass

Boolean = Union[NewType('Boolean', bool), None]
ID = Union[NewType('ID', str), None]
UnsignedInt64 = Union[NewType('UnsignedInt64', int), None]
String = Union[NewType('String', str), None]
Int = Union[NewType('Int', int), None]
URL = Union[NewType('URL', str), None]
DateTime = Union[datetime, None]

