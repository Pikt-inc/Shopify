from typing import Optional

from shopify_sdk.gql.core.types import ID, ProductStatus
from .manager import StatusUpsertManager

def upsert_inventory_status(
    to_active: list[ID] = [],
    to_archive: list[ID] = [],
    to_draft: list[ID] = [],
    fallback_status: Optional[ProductStatus] = ProductStatus.ARCHIVED,
) -> bool:
    """
    Upserts product statuses in bulk.

    Args:
        to_active (list[ID], optional): List of product IDs to set as ACTIVE. Defaults to [].
        to_archive (list[ID], optional): List of product IDs to set as ARCHIVED. Defaults to [].
        to_draft (list[ID], optional): List of product IDs to set as DRAFT. Defaults to [].
        fallback_status (Optional[ProductStatus], optional): Fallback status for diff IDs. Defaults to ProductStatus.ARCHIVED.

    Returns:
        bool: True if all operations were successful, False otherwise.
    """
    return StatusUpsertManager.inventory_status_sync(
        to_active=to_active,
        to_archive=to_archive,
        to_draft=to_draft,
        fallback_status=fallback_status,
    )   

__all__ = ["upsert_inventory_status"]