from collections.abc import Sequence
from typing import TYPE_CHECKING
from pydantic import BaseModel
from shopify_sdk import client

if TYPE_CHECKING:
    from shopify_sdk.gql.core.types import ID
from shopify_sdk.gql.core.types.connections import MediaConnection


class MediaManager(BaseModel):
    def stage_local_images(self, images: Sequence["LocalProductImage"]) -> "ProductImageStageResult":
        """Stage local image bytes for immediate use in a product mutation.

        :param images: Ordered local product images.
        :returns: Ordered staged Shopify resource URLs.
        """

        from shopify_sdk.common.product.image_upload import ProductImageStager

        return ProductImageStager().stage(images)

    def images(
        self,
        product_id: "ID",
    ) -> "MediaConnection":
        from shopify_sdk.gql.core.types import ProductIdentifierInput
        from shopify_sdk.gql.queries import productByIdentifier

        identifier = ProductIdentifierInput(id=product_id, handle=None)
        product = productByIdentifier(
            identifier=identifier,
            field_inclusions={
                "Product": {"media"},
                "MediaConnection": {"nodes"},
                "Media": {"id", "mediaContentType", "alt", "previewImage"},
                "Image": {"url", "width", "height"},
            },
        ).execute(client=client)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")

        return product.media

    def delete(self, media_ids: "ID | list[ID]") -> bool:
        from shopify_sdk.gql.mutations import fileDelete

        if not media_ids:
            return True

        if isinstance(media_ids, str):
            media_id_list = [media_ids]
        else:
            media_id_list = list(media_ids)

        payload = fileDelete(
            fileIds=media_id_list,
            field_inclusions={
                "FileDeletePayload": {"deletedFileIds", "userErrors"},
                "UserError": {"field", "message"},
            },
        ).execute(client=client)
        if payload is None:
            raise ValueError("Media deletion failed; no payload returned.")
        user_errors = getattr(payload, "userErrors", []) or []
        if user_errors:
            messages = ", ".join(error.message for error in user_errors)
            raise ValueError(f"Media deletion failed: {messages}")
        deleted_ids = getattr(payload, "deletedFileIds", None) or []
        missing = set(media_id_list) - set(deleted_ids)
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ValueError(
                f"Media deletion failed; missing deleted ids: {missing_list}"
            )
        return True


if TYPE_CHECKING:
    from shopify_sdk.common.product.image_upload import (
        LocalProductImage,
        ProductImageStageResult,
    )
