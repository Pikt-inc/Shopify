import logging
from typing import Optional
from pydantic import model_validator, Field, BaseModel

from shopify_sdk.gql.core.types import ID

logger = logging.getLogger(__name__)


class InventorySyncInput(BaseModel):
    """
    Input object used to sync shopify inventory based on product status.
    """

    active: list[ID] = Field(default_factory=list)
    archived: list[ID] = Field(default_factory=list)
    draft: list[ID] = Field(default_factory=list)
    scope_query: Optional[str] = None

    @classmethod
    def merged_ids(cls, values: dict) -> list[ID]:
        """
        Returns a merged list of all IDs in the input object.
        """
        return list(
            set(values.get("active", []))
            | set(values.get("archived", []))
            | set(values.get("draft", []))
        )

    @model_validator(mode="before")
    def validate_ids(cls, values):
        """
        Validates that the IDs provided are valid Shopify Product IDs.
        Deduplicates IDs within each list.
        Validate that each ID exists in the store.
        Raises ValueError if any ID is invalid.
        Validate that IDs are not shared between lists.
        """
        for field_name in ["active", "archived", "draft"]:
            status_id_list = values.get(field_name, [])
            for _id in status_id_list:
                if not isinstance(_id, str) or not _id.startswith(
                    "gid://shopify/Product"
                ):
                    logger.error(f"Invalid Shopify ID in '{field_name}': {_id}")
                    raise ValueError(f"Invalid Shopify ID in '{field_name}': {_id}")

            values[field_name] = list(set(status_id_list))

        for field_a, field_b in [
            ("active", "archived"),
            ("active", "draft"),
            ("archived", "draft"),
        ]:
            overlap = set(values.get(field_a, [])) & set(values.get(field_b, []))
            if overlap:
                logger.error(
                    f"The following IDs are present in both '{field_a}' and '{field_b}': {overlap}"
                )
                raise ValueError(
                    f"The following IDs are present in both '{field_a}' and '{field_b}': {overlap}"
                )

        return values
