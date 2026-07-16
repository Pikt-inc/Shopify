"""Python 3.10-compatible string enumeration base."""

from enum import Enum


class StringEnum(str, Enum):
    """Provide the string formatting behavior of :class:`enum.StrEnum`."""

    def __str__(self) -> str:
        """Return the raw string value.

        :returns: Enum value as a string.
        """

        return str.__str__(self)


__all__ = ["StringEnum"]
