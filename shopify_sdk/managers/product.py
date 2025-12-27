from pydantic import BaseModel, Field
import logging
from typing import Optional, List
from shopify_sdk.gql.core.types import ID, ProductStatus
from shopify_sdk.common.types import ProxyProduct
from .product_bulk import BulkProductManager

logger = logging.getLogger(__name__)


class ProductManager(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    bulk: BulkProductManager = Field(default_factory=BulkProductManager)
    
    def archive(
        self,
        id: ID = None,
        sku: str = None,
        product: ProxyProduct = None
    ):
        from shopify_sdk.common.product.archive import (
            archive_product_by_id, archive_product_by_sku
        )
        id = id or (product.id if product else None)
        sku = sku or (product.sku if product else None)
        if not id and not sku:
            logger.warning("Either 'id' or 'sku' must be provided to archive a product.")
            raise ValueError("Either 'id' or 'sku' must be provided to archive a product.")
        
        if id:
            return archive_product_by_id(product_id=id)
        else:
            return archive_product_by_sku(sku=sku)