from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from shopify_sdk.common.product.publish import list_publications
from shopify_sdk.common.store.locations import get_locations
from shopify_sdk.gql.core.pagination import (
    DEFAULT_PAGE_SIZE,
    CursorPager,
    CursorPageInfo,
    CursorPaginationError,
    CursorPaginationLimitError,
)
from shopify_sdk.gql.core.types.connections import (
    LocationConnection,
    PublicationConnection,
)
from shopify_sdk.gql.versions.v2025_10.types.objects import PageInfo as PageInfo2025
from shopify_sdk.managers.store import StoreManager


@dataclass(frozen=True)
class FakePage:
    nodes: tuple[str, ...]
    page_info: CursorPageInfo


class FakeQuery:
    def __init__(self, page: LocationConnection | PublicationConnection) -> None:
        """Store the connection returned when the fake query executes."""
        self._page = page

    def execute(
        self,
        client: object,
    ) -> LocationConnection | PublicationConnection:
        """Return the configured test connection without using a client."""
        return self._page


def get_fake_page_info(page: FakePage) -> CursorPageInfo:
    """Return the pager cursor state from a fake page."""
    return page.page_info


def is_fake_page_empty(page: FakePage) -> bool:
    """Return whether a fake page has no nodes."""
    return not page.nodes


def make_location_connection(
    identifier: str,
    *,
    has_next_page: bool,
    end_cursor: str | None,
) -> LocationConnection:
    """Build a minimal location connection without unrelated model fields."""
    return LocationConnection.model_construct(
        nodes=[SimpleNamespace(id=identifier)],
        edges=[SimpleNamespace(cursor=f"edge-{identifier}")],
        pageInfo=SimpleNamespace(
            hasNextPage=has_next_page,
            endCursor=end_cursor,
        ),
    )


def make_publication_connection(
    identifier: str,
    *,
    has_next_page: bool,
    end_cursor: str | None,
) -> PublicationConnection:
    """Build a minimal publication connection without unrelated model fields."""
    return PublicationConnection.model_construct(
        nodes=[SimpleNamespace(id=identifier)],
        edges=[SimpleNamespace(cursor=f"edge-{identifier}")],
        pageInfo=SimpleNamespace(
            hasNextPage=has_next_page,
            endCursor=end_cursor,
        ),
    )


class TestCursorPager:
    def test_2025_page_info_accepts_terminal_null_cursors(self) -> None:
        """Accept Shopify's null cursor fields on a terminal 2025-10 page."""
        page_info = PageInfo2025.model_validate(
            {
                "hasNextPage": False,
                "hasPreviousPage": False,
                "startCursor": None,
                "endCursor": None,
            }
        )

        assert page_info.endCursor is None
        assert page_info.startCursor is None

    def test_collects_all_pages(self) -> None:
        """Collect every page by advancing the returned end cursor."""
        pages = {
            None: FakePage(("first",), CursorPageInfo(True, "cursor-one")),
            "cursor-one": FakePage(("second",), CursorPageInfo(False, None)),
        }
        requested_cursors: list[str | None] = []

        def fetch_page(cursor: str | None) -> FakePage:
            """Return the fake page associated with the requested cursor."""
            requested_cursors.append(cursor)
            return pages[cursor]

        result = CursorPager(
            fetch_page=fetch_page,
            get_page_info=get_fake_page_info,
            is_empty_page=is_fake_page_empty,
        ).collect()

        assert requested_cursors == [None, "cursor-one"]
        assert [node for page in result for node in page.nodes] == ["first", "second"]

    def test_rejects_missing_next_cursor(self) -> None:
        """Reject a continuation response that lacks an end cursor."""
        page = FakePage(("first",), CursorPageInfo(True, None))

        def fetch_page(cursor: str | None) -> FakePage:
            """Return the invalid fake page."""
            return page

        with pytest.raises(CursorPaginationError, match="without an endCursor"):
            CursorPager(fetch_page, get_fake_page_info, is_fake_page_empty).collect()

    def test_rejects_repeated_cursor(self) -> None:
        """Reject a cursor sequence that would request the same page forever."""
        pages = {
            None: FakePage(("first",), CursorPageInfo(True, "cursor-one")),
            "cursor-one": FakePage(("second",), CursorPageInfo(True, "cursor-one")),
        }

        def fetch_page(cursor: str | None) -> FakePage:
            """Return the fake page associated with the requested cursor."""
            return pages[cursor]

        with pytest.raises(CursorPaginationError, match="repeated pagination cursor"):
            CursorPager(fetch_page, get_fake_page_info, is_fake_page_empty).collect()

    def test_rejects_empty_continuation_page(self) -> None:
        """Reject empty pages that claim an additional page exists."""
        page = FakePage((), CursorPageInfo(True, "cursor-one"))

        def fetch_page(cursor: str | None) -> FakePage:
            """Return the invalid empty page."""
            return page

        with pytest.raises(CursorPaginationError, match="empty page"):
            CursorPager(fetch_page, get_fake_page_info, is_fake_page_empty).collect()

    def test_enforces_configured_page_limit(self) -> None:
        """Reject pagination sequences that exceed the caller's safety limit."""
        page = FakePage(("first",), CursorPageInfo(True, "cursor-one"))

        def fetch_page(cursor: str | None) -> FakePage:
            """Return a page that always advertises a successor."""
            return page

        with pytest.raises(CursorPaginationLimitError, match="1-page safety limit"):
            CursorPager(
                fetch_page,
                get_fake_page_info,
                is_fake_page_empty,
                max_pages=1,
            ).collect()


class TestTopLevelConnectionPagination:
    def test_store_locations_aggregates_all_pages(self) -> None:
        """Aggregate location nodes and edges while preserving final page information."""
        pages = {
            None: make_location_connection(
                "location-one",
                has_next_page=True,
                end_cursor="cursor-one",
            ),
            "cursor-one": make_location_connection(
                "location-two",
                has_next_page=False,
                end_cursor=None,
            ),
        }
        requested_arguments: list[dict[str, object]] = []

        def locations_query(**kwargs: object) -> FakeQuery:
            """Return a fake query for the requested location cursor."""
            requested_arguments.append(kwargs)
            return FakeQuery(pages[kwargs["after"]])

        with patch("shopify_sdk.gql.queries.locations", side_effect=locations_query):
            result = StoreManager().locations

        assert [location.id for location in result.nodes] == [
            "location-one",
            "location-two",
        ]
        assert [edge.cursor for edge in result.edges] == [
            "edge-location-one",
            "edge-location-two",
        ]
        assert [arguments["after"] for arguments in requested_arguments] == [
            None,
            "cursor-one",
        ]
        assert all(arguments["first"] == DEFAULT_PAGE_SIZE for arguments in requested_arguments)

    def test_store_publications_aggregates_all_pages(self) -> None:
        """Aggregate publication nodes and edges across every cursor page."""
        pages = {
            None: make_publication_connection(
                "publication-one",
                has_next_page=True,
                end_cursor="cursor-one",
            ),
            "cursor-one": make_publication_connection(
                "publication-two",
                has_next_page=False,
                end_cursor=None,
            ),
        }

        def publications_query(**kwargs: object) -> FakeQuery:
            """Return a fake query for the requested publication cursor."""
            return FakeQuery(pages[kwargs["after"]])

        with patch(
            "shopify_sdk.gql.queries.publications",
            side_effect=publications_query,
        ):
            result = StoreManager().publications

        assert [publication.id for publication in result.nodes] == [
            "publication-one",
            "publication-two",
        ]
        assert [edge.cursor for edge in result.edges] == [
            "edge-publication-one",
            "edge-publication-two",
        ]

    def test_get_locations_returns_all_location_pages(self) -> None:
        """Return all locations through the common location helper."""
        pages = {
            None: make_location_connection(
                "location-one",
                has_next_page=True,
                end_cursor="cursor-one",
            ),
            "cursor-one": make_location_connection(
                "location-two",
                has_next_page=False,
                end_cursor=None,
            ),
        }

        def locations_query(**kwargs: object) -> FakeQuery:
            """Return a fake query for the requested location cursor."""
            return FakeQuery(pages[kwargs["after"]])

        with patch(
            "shopify_sdk.common.store.locations.locations",
            side_effect=locations_query,
        ):
            result = get_locations()

        assert [location.id for location in result] == ["location-one", "location-two"]

    def test_list_publications_returns_all_pages(self) -> None:
        """Return every identified publication through the product helper."""
        pages = {
            None: make_publication_connection(
                "publication-one",
                has_next_page=True,
                end_cursor="cursor-one",
            ),
            "cursor-one": make_publication_connection(
                "publication-two",
                has_next_page=False,
                end_cursor=None,
            ),
        }
        requested_arguments: list[dict[str, object]] = []

        def publications_query(**kwargs: object) -> FakeQuery:
            """Return a fake query for the requested publication cursor."""
            requested_arguments.append(kwargs)
            return FakeQuery(pages[kwargs["after"]])

        with patch(
            "shopify_sdk.common.product.publish.publications_query",
            side_effect=publications_query,
        ):
            result = list_publications(page_size=25)

        assert [publication.id for publication in result] == [
            "publication-one",
            "publication-two",
        ]
        assert [arguments["after"] for arguments in requested_arguments] == [
            None,
            "cursor-one",
        ]
        assert all(arguments["first"] == 25 for arguments in requested_arguments)
