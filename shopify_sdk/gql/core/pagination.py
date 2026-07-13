"""Safe cursor pagination primitives for Shopify GraphQL connections."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar


DEFAULT_PAGE_SIZE = 250
"""Starting page size; Shopify's Admin GraphQL connection maximum."""

DEFAULT_MAX_PAGES = 1_000
"""Starting safety cap; calibrate from observed production page counts."""

PageT = TypeVar("PageT")


class CursorPaginationError(ValueError):
    """Raised when Shopify cursor pagination returns an invalid page sequence."""


class CursorPaginationLimitError(CursorPaginationError):
    """Raised when pagination exceeds the configured page safety limit."""


@dataclass(frozen=True)
class CursorPageInfo:
    """Cursor state extracted from a single GraphQL connection response."""

    has_next_page: bool
    end_cursor: str | None


class SupportsCursorPageInfo(Protocol):
    """Describe the cursor fields exposed by Shopify PageInfo models."""

    hasNextPage: bool
    endCursor: str | None


class CursorConnection(Protocol):
    """Describe the connection fields required for safe cursor collection."""

    @property
    def pageInfo(self) -> SupportsCursorPageInfo:
        """Return the page cursor state."""

    @property
    def nodes(self) -> Sequence[object]:
        """Return the current page's nodes."""


def connection_page_info(connection: CursorConnection) -> CursorPageInfo:
    """Map a Shopify connection's camel-case cursor fields to pager state."""
    return CursorPageInfo(
        has_next_page=connection.pageInfo.hasNextPage,
        end_cursor=connection.pageInfo.endCursor,
    )


def is_empty_connection(connection: CursorConnection) -> bool:
    """Return whether a Shopify connection contains no nodes."""
    return not connection.nodes


class CursorPager(Generic[PageT]):
    """Collect GraphQL connection pages while enforcing cursor safety invariants."""

    def __init__(
        self,
        fetch_page: Callable[[str | None], PageT],
        get_page_info: Callable[[PageT], CursorPageInfo],
        is_empty_page: Callable[[PageT], bool],
        *,
        max_pages: int = DEFAULT_MAX_PAGES,
    ) -> None:
        """Initialize pagination collaborators and validate the page safety limit."""
        if max_pages < 1:
            raise ValueError("max_pages must be at least one.")
        self._fetch_page = fetch_page
        self._get_page_info = get_page_info
        self._is_empty_page = is_empty_page
        self._max_pages = max_pages

    def collect(self) -> list[PageT]:
        """Fetch every page or raise when the cursor sequence is invalid."""
        pages: list[PageT] = []
        cursor: str | None = None
        seen_cursors: set[str] = set()
        for _ in range(self._max_pages):
            page = self._fetch_page(cursor)
            pages.append(page)
            cursor = self._next_cursor(page, seen_cursors)
            if cursor is None:
                return pages
        raise CursorPaginationLimitError(
            f"Pagination exceeded the {self._max_pages}-page safety limit."
        )

    def _next_cursor(self, page: PageT, seen_cursors: set[str]) -> str | None:
        """Validate a page response and return the cursor for its successor."""
        page_info = self._get_page_info(page)
        if not page_info.has_next_page:
            return None
        if self._is_empty_page(page):
            raise CursorPaginationError("Received an empty page with hasNextPage=True.")
        return self._validate_next_cursor(page_info.end_cursor, seen_cursors)

    @staticmethod
    def _validate_next_cursor(
        cursor: str | None,
        seen_cursors: set[str],
    ) -> str:
        """Return a new cursor or reject missing and repeated cursor values."""
        if not cursor:
            raise CursorPaginationError("Received hasNextPage=True without an endCursor.")
        if cursor in seen_cursors:
            raise CursorPaginationError(f"Received repeated pagination cursor: {cursor!r}.")
        seen_cursors.add(cursor)
        return cursor
