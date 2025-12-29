from __future__ import annotations

from typing import Any, Optional

from shopify_sdk import client
from shopify_sdk.gql import productCreateMedia, fileUpdate
from shopify_sdk.gql.core.types import ID
from shopify_sdk.gql.core.types.input_objects import (
    CreateMediaInput,
    FileUpdateInput,
    ProductIdentifierInput,
)
from shopify_sdk.gql.queries import productByIdentifier

MEDIA_PAGE_SIZE = 100


def create_product_media(product_id: str, image_urls: list[str]) -> bool:
    """Create media (images) for a product using the provided image URLs."""
    if not image_urls:
        return True  # No images to add, return success

    media_inputs: list[CreateMediaInput] = []
    for url in image_urls:
        media_inputs.append(
            CreateMediaInput(
                alt=None,  # Alt text can be extended in the future
                mediaContentType="IMAGE",
                originalSource=url,
            )
        )

    try:
        result: dict[str, Any] = productCreateMedia(
            media=media_inputs,
            productId=ID(product_id),
        ).execute(client=client)

        media_result = result.get("media")
        if media_result is None:
            raise ValueError("Product media creation returned no media payload.")
        return True
    except Exception as e:
        raise ValueError(f"Product media creation failed: {e}")


def _collect_media_ids(product_id: str) -> list[str]:
    """Walk through the media connection and return every media ID for the product."""
    media_ids: list[str] = []
    after: Optional[str] = None

    while True:
        media_connection = _fetch_media_connection(product_id, after)
        if not media_connection:
            break

        nodes = getattr(media_connection, "nodes", None) or []
        media_ids.extend(str(node.id) for node in nodes if getattr(node, "id", None))

        page_info = getattr(media_connection, "pageInfo", None)
        if not page_info or not getattr(page_info, "hasNextPage", False):
            break

        after = getattr(page_info, "endCursor", None)
        if not after:
            break

    return media_ids


def _fetch_media_connection(product_id: str, after: Optional[str]) -> Any:
    """Fetch one page of a product's media connection."""
    connection_args: dict[str, dict[str, Any]] = {"media": {"first": MEDIA_PAGE_SIZE}}
    if after:
        connection_args["media"]["after"] = after

    product = productByIdentifier(
        identifier=ProductIdentifierInput(id=product_id, handle=None),
        field_inclusions={
            "Product": {"media"},
            "MediaConnection": {"nodes", "pageInfo"},
            "Media": {"id"},
            "PageInfo": {"hasNextPage", "endCursor"},
        },
        connection_arguments=connection_args,
    ).execute(client=client)

    return getattr(product, "media", None)


def delete_product_media(product_id: str) -> bool:
    """Remove all media objects that are currently associated with the product."""
    media_ids = _collect_media_ids(product_id)
    if not media_ids:
        return True

    try:
        file_inputs = [
            FileUpdateInput(
                id=ID(media_id),
                referencesToRemove=[ID(product_id)],
            )
            for media_id in media_ids
        ]

        result: dict[str, Any] = fileUpdate(
            files=file_inputs,
        ).execute(client=client)
    except Exception as e:
        raise ValueError(f"Product media deletion failed: {e}")

    updated_files = result.get("files", [])
    if len(updated_files) != len(media_ids):
        raise ValueError(
            "Not all product media entries were disassociated from the product."
        )

    return True


def set_product_images(product_id: str, images: Optional[list[str]]) -> bool:
    """Helper function to replace a product's media collection."""
    if images is None:
        return True  # No update requested

    delete_product_media(product_id)

    if not images:
        return True  # Images explicitly cleared

    create_product_media(
        product_id=product_id,
        image_urls=images,
    )
    return True
