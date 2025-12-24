import logging
from pydantic import model_validator, Field, BaseModel

from shopify_sdk.gql.core.types import ID, Product
from shopify_sdk.gql.queries import products
from shopify_sdk.tools.bulk import run_bulk_query

logger = logging.getLogger(__name__)

class InventorySyncInput(BaseModel):
    """
    Input object used to sync shopify inventory based on product status.
    """
    active: list[ID] = Field(default_factory=list)
    archived: list[ID] = Field(default_factory=list)
    draft: list[ID] = Field(default_factory=list)

    @classmethod
    def merged_ids(cls, values: dict) -> list[ID]:
        """
        Returns a merged list of all IDs in the input object.
        """
        return list(set(values.get("active", [])) | set(values.get("archived", [])) | set(values.get("draft", [])))
    
    @classmethod
    def valid_ids(cls) -> list[ID]:
        """
        Returns a list of all product ids currently in the store.
        We need to validate that all provided IDs are valid Shopify Product IDs.
        We can do this via a bulk query to fetch all product IDs.
        """
        bulk_query = products(
            field_exclusions={
                "Product": Product.fields_except(
                    exclude={"id"}
                )
            }
        )
        _ids: list[ID] = []
        for line in run_bulk_query(bulk_query, verbose=True):
            product_id = line.get('id', None)
            if not product_id:
                logger.warning("Encountered product with no ID during validation.")
                raise ValueError("Encountered product with no ID during validation.")
            _ids.append(product_id)
        return _ids

    @model_validator(mode="before")
    def validate_ids(cls, values):
        """
        Validates that the IDs provided are valid Shopify Product IDs.
        Deduplicates IDs within each list.
        Validate that each ID exists in the store.
        Raises ValueError if any ID is invalid.
        Validate that IDs are not shared between lists.
        """
        for field_name in ['active', 'archived', 'draft']:
            status_id_list = values.get(field_name, [])
            for _id in status_id_list:
                if not isinstance(_id, str) or not _id.startswith("gid://shopify/Product"):
                    logger.error(f"Invalid Shopify ID in '{field_name}': {_id}")
                    raise ValueError(f"Invalid Shopify ID in '{field_name}': {_id}")

            values[field_name] = list(set(status_id_list))
                
        merged = set(cls.merged_ids(values))
        diff = merged - set(cls.valid_ids())
        if diff:
            raise ValueError(f"The following IDs were not found in the target store: {diff}")
        
        for field_a, field_b in [('active', 'archived'), ('active', 'draft'), ('archived', 'draft')]:
            overlap = set(values.get(field_a, [])) & set(values.get(field_b, []))
            if overlap:
                logger.error(f"The following IDs are present in both '{field_a}' and '{field_b}': {overlap}")
                raise ValueError(f"The following IDs are present in both '{field_a}' and '{field_b}': {overlap}")
                
        return values