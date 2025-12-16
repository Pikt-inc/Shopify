from __future__ import annotations

from typing import Any

from shopify_sdk import client
from shopify_sdk.gql import productCreateMedia
from shopify_sdk.gql.core.types import ID
from shopify_sdk.gql.core.types.input_objects import CreateMediaInput


def create_product_media(
    product_id: str,
    image_urls: list[str]
) -> bool:
    """Create media (images) for a product using the provided image URLs."""
    if not image_urls:
        return True  # No images to add, return success
    
    media_inputs = []
    for url in image_urls:
        media_input = CreateMediaInput(
            alt="",  # Can be extended to support alt text in the future
            mediaContentType="IMAGE",
            originalSource=url
        )
        media_inputs.append(media_input)
    
    try:
        result: dict[str, Any] = productCreateMedia(
            media=media_inputs,
            productId=ID(product_id)
        ).execute(client=client)
        
        # Check if media was created successfully
        media_result = result.get('media', [])
        return len(media_result) > 0 or len(image_urls) == 0
    except Exception as e:
        raise ValueError(f"Product media creation failed: {e}")
