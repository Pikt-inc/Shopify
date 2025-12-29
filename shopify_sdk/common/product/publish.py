from __future__ import annotations

from datetime import datetime
from typing import Sequence

from shopify_sdk import client
from shopify_sdk.gql import productPublish, publications as publications_query
from shopify_sdk.gql.core.types import (
    ProductPublicationInput,
    ProductPublishInput,
    Publication,
)

from .types import ProductActionResponse


def list_publications(page_size: int = 20) -> list[Publication]:
    """
    Return all available sales channel publications (id and name).
    Pagination is handled internally using the provided page_size.
    """
    publications: list[Publication] = []
    after: str | None = None

    while True:
        connection = publications_query(
            first=page_size,
            after=after,
            field_inclusions={
                "Publication": {"id", "name"},
                "PageInfo": {"hasNextPage", "endCursor"},
            },
            field_exclusions={
                "PublicationConnection": {"edges"},
            },
        ).execute(client=client)

        if not connection:
            break

        publications.extend(
            [
                node
                for node in getattr(connection, "nodes", []) or []
                if getattr(node, "id", None)
            ]
        )

        page_info = getattr(connection, "pageInfo", None)
        has_next = (
            bool(getattr(page_info, "hasNextPage", False)) if page_info else False
        )
        after = getattr(page_info, "endCursor", None) if has_next else None
        if not has_next:
            break

    return publications


def build_product_publications(
    publication_ids: Sequence[str],
    publish_date: datetime | None = None,
) -> list[ProductPublicationInput]:
    """Create ProductPublicationInput models for the provided publication ids."""
    return [
        ProductPublicationInput(
            publicationId=pub_id,
            publishDate=publish_date,
        )
        for pub_id in publication_ids
    ]


def publish_product_to_publications(
    product_id: str,
    publication_ids: Sequence[str],
    *,
    publish_date: datetime | None = None,
    sku: str | None = None,
) -> ProductActionResponse:
    """Publish a product to the specified publication ids."""
    success = False
    message: str | None = None
    try:
        publication_inputs = build_product_publications(publication_ids, publish_date)
        if not publication_inputs:
            raise ValueError("No publication ids provided for publishing.")

        publish_input = ProductPublishInput(
            id=product_id,
            productPublications=publication_inputs,
        )
        result = productPublish(input=publish_input).execute(client=client)
        success = bool(result)
        if not success:
            message = f"Failed to publish product '{product_id}'."
    except Exception as e:
        message = str(e)
        success = False

    return ProductActionResponse(
        action="publish",
        success=success,
        message=message,
        sku=sku,
        product_id=product_id,
    )


def publish_product_to_all_publications(
    product_id: str,
    *,
    publication_page_size: int = 20,
    publish_date: datetime | None = None,
    sku: str | None = None,
) -> ProductActionResponse:
    """Publish a product to every available publication."""
    try:
        publications = list_publications(page_size=publication_page_size)
        publication_ids: list[str] = []
        for pub in publications:
            pub_id = getattr(pub, "id", None)
            if pub_id:
                publication_ids.append(str(pub_id))
        if not publication_ids:
            raise ValueError("No publications available to publish to.")
    except Exception as e:
        return ProductActionResponse(
            action="publish",
            success=False,
            message=str(e),
            sku=sku,
            product_id=product_id,
        )

    return publish_product_to_publications(
        product_id=product_id,
        publication_ids=publication_ids,
        publish_date=publish_date,
        sku=sku,
    )
