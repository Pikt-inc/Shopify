from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator, Optional, cast
from pydantic import BaseModel, Field

from shopify_sdk.api_versions import resolve_api_version
from shopify_sdk.gql.core.pagination import (
    DEFAULT_PAGE_SIZE,
    CursorPager,
    connection_page_info,
    is_empty_connection,
)

from .products import ProductManager
from .orders import OrderManager
from .delivery import DeliveryManager
from .map import MapManager
from .webhooks import WebhookManager

if TYPE_CHECKING:
    from shopify_sdk.gql.core.types.connections import (
        LocationConnection,
        PublicationConnection,
    )
    from shopify_sdk.gql.core.types.base import ID
    from shopify_sdk.gql.core.client.retry import ShopifyRetryPolicy


class StoreManager(BaseModel):
    products: ProductManager = Field(default_factory=ProductManager)
    orders: OrderManager = Field(default_factory=OrderManager)
    delivery: DeliveryManager = Field(default_factory=DeliveryManager)
    map: "MapManager" = Field(default_factory=lambda: MapManager())
    webhooks: WebhookManager = Field(default_factory=WebhookManager)
    model_config = {
        "arbitrary_types_allowed": True,
    }

    @contextmanager
    def credentials_context(
        self,
        shop_domain: str,
        access_token: str,
        api_version: Optional[str] = None,
        retry_policy: "ShopifyRetryPolicy | None" = None,
    ) -> Iterator["StoreManager"]:
        """Yield the manager with context-scoped credentials and retry policy.

        :param shop_domain: Shopify shop domain.
        :param access_token: Shopify Admin API access token.
        :param api_version: Optional Shopify Admin GraphQL API version.
        :param retry_policy: Optional policy for safe GraphQL query retries.
        """
        from shopify_sdk import client_context

        version = resolve_api_version(api_version)
        with client_context(
            shop_domain=shop_domain,
            access_token=access_token,
            api_version=version,
            retry_policy=retry_policy,
        ):
            yield self

    @property
    def locations(self) -> "LocationConnection":
        """Return every location available to the current shop."""
        pages: list["LocationConnection"] = CursorPager(
            fetch_page=self._fetch_locations_page,
            get_page_info=connection_page_info,
            is_empty_page=is_empty_connection,
        ).collect()
        return self._combine_location_pages(pages)

    @staticmethod
    def _combine_location_pages(
        pages: list["LocationConnection"],
    ) -> "LocationConnection":
        """Combine paginated location connections without changing their public shape."""
        if not pages:
            raise ValueError("Shopify returned no location connection pages.")
        return pages[0].model_copy(
            update={
                "nodes": [node for page in pages for node in page.nodes],
                "edges": [edge for page in pages for edge in page.edges],
                "pageInfo": pages[-1].pageInfo,
            }
        )

    @staticmethod
    def _fetch_locations_page(after: str | None) -> "LocationConnection":
        """Fetch one maximum-sized location page after an optional cursor."""
        from shopify_sdk import client
        from shopify_sdk.gql.queries import locations

        query = locations(
            first=DEFAULT_PAGE_SIZE,
            after=after,
            field_inclusions={
                "Location": set(
                    {
                        "id",
                        "name",
                        "address",
                        "city",
                        "country",
                        "province",
                        "zip",
                        "active",
                        "legacy",
                        "inventoryLevels",
                    }
                )
            },
        )
        return cast("LocationConnection", query.execute(client))

    @property
    def location_ids(self) -> list["ID"]:
        loc_ids = [loc.id for loc in self.locations.nodes if loc.id]
        return loc_ids

    @property
    def publications(self) -> "PublicationConnection":
        """Return every publication available to the current shop."""
        pages: list["PublicationConnection"] = CursorPager(
            fetch_page=self._fetch_publications_page,
            get_page_info=connection_page_info,
            is_empty_page=is_empty_connection,
        ).collect()
        return self._combine_publication_pages(pages)

    @staticmethod
    def _combine_publication_pages(
        pages: list["PublicationConnection"],
    ) -> "PublicationConnection":
        """Combine paginated publication connections without changing their public shape."""
        if not pages:
            raise ValueError("Shopify returned no publication connection pages.")
        return pages[0].model_copy(
            update={
                "nodes": [node for page in pages for node in page.nodes],
                "edges": [edge for page in pages for edge in page.edges],
                "pageInfo": pages[-1].pageInfo,
            }
        )

    @staticmethod
    def _fetch_publications_page(after: str | None) -> "PublicationConnection":
        """Fetch one maximum-sized publication page after an optional cursor."""
        from shopify_sdk import client
        from shopify_sdk.gql.queries import publications

        query = publications(
            first=DEFAULT_PAGE_SIZE,
            after=after,
            field_inclusions={
                "Publication": set({"id", "name", "status", "publishedAt", "updatedAt"})
            },
        )
        return cast("PublicationConnection", query.execute(client))


store = StoreManager()
