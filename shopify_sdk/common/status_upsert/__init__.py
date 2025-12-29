from typing import Optional

from shopify_sdk.gql.core.types import ID, ProductStatus
from .manager import StatusUpsertManager

def upsert_inventory_status(
    to_active: Optional[list[ID]] = None,
    to_archive: Optional[list[ID]] = None,
    to_draft: Optional[list[ID]] = None,
    fallback_status: Optional[ProductStatus] = ProductStatus.ARCHIVED,
) -> bool:
    """
    Upserts product statuses in bulk.

    Args:
        to_active (Optional[list[ID]], optional): List of product IDs to set as ACTIVE. Defaults to None
            (treated as empty list).
        to_archive (Optional[list[ID]], optional): List of product IDs to set as ARCHIVED. Defaults to None
            (treated as empty list).
        to_draft (Optional[list[ID]], optional): List of product IDs to set as DRAFT. Defaults to None
            (treated as empty list).
        fallback_status (Optional[ProductStatus], optional): Status for product IDs in the store that
            are not in any provided list ("diff IDs"). Defaults to ProductStatus.ARCHIVED.

    Returns:
        bool: True if all operations were successful; False if any bulk status update fails.

    Raises:
        ValueError: If validation fails.
    """
    if to_active is None:
        to_active = []
    if to_archive is None:
        to_archive = []
    if to_draft is None:
        to_draft = []
    return StatusUpsertManager.inventory_status_sync(
        to_active=to_active,
        to_archive=to_archive,
        to_draft=to_draft,
        fallback_status=fallback_status,
    )

__all__ = ["upsert_inventory_status"]
