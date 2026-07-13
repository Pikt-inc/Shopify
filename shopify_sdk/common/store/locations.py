from typing import cast

from shopify_sdk import client
from shopify_sdk.gql.core.pagination import (
    DEFAULT_PAGE_SIZE,
    CursorPager,
    connection_page_info,
    is_empty_connection,
)
from shopify_sdk.gql.core.types.connections import LocationConnection
from shopify_sdk.gql.core.types.enums import LocationSortKeys
from shopify_sdk.gql.core.types.objects import Location
from shopify_sdk.gql.queries import locations


def get_locations() -> list[Location]:
    """Return every location ordered by name for the current shop."""
    pages: list[LocationConnection] = CursorPager(
        fetch_page=_fetch_locations_page,
        get_page_info=connection_page_info,
        is_empty_page=is_empty_connection,
    ).collect()
    location_nodes = [node for page in pages for node in page.nodes]

    if not location_nodes:
        raise ValueError("No locations found.")

    return location_nodes


def _fetch_locations_page(after: str | None) -> LocationConnection:
    """Fetch one maximum-sized location page after an optional cursor."""
    return cast(
        LocationConnection,
        locations(
            first=DEFAULT_PAGE_SIZE,
            after=after,
            sortKey=LocationSortKeys.NAME,
            reverse=False,
        ).execute(client=client),
    )
