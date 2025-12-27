from pydantic import BaseModel, Field
import logging
from typing import Optional, List
from shopify_sdk.gql.core.types import ID, ProductStatus
from shopify_sdk.common.types import ProxyProduct

logger = logging.getLogger(__name__)

class BulkProductManager:

    def bulk_status_set(
        self,
        to_active: Optional[list[ID]] = None,
        to_archive: Optional[list[ID]] = None,
        to_draft: Optional[list[ID]] = None,
        fallback_status: Optional[ProductStatus] = None,
    ) -> bool:
        """
        Public method to bulk update product statuses of all input items or all items in the store.
        """
        from shopify_sdk.common import upsert_inventory_status
        if not any([to_active, to_archive, to_draft]):
            logger.warning("No products provided for status update.")
            return False
        return upsert_inventory_status(
            to_active=to_active,
            to_archive=to_archive,
            to_draft=to_draft,
            fallback_status=fallback_status,
        )
    
    def create(
        self,
        products: List[ProxyProduct]
    ) -> bool:
        from shopify_sdk.common.product import execute_bulk_product_create
        from shopify_sdk.common.variant import execute_bulk_variant_create
        from shopify_sdk.common.resolver import ProductIdSkuResolver
        if not products or not isinstance(products, list):
            logger.warning("No products provided for bulk creation.")
            return False
        
        # execute_bulk_product_create(products)
        # for product in products:
        #     print(product.title, product.id)
        # execute_bulk_variant_create(products)
        from shopify_sdk.common.product.bulk.set import execute_bulk_product_set
        execute_bulk_product_set(products)
        # print(f"Resolved {len(resolved_products.id_sku_map)} product IDs based on")

        # now set variants
    

    def update(
        self,
        products: List[ProxyProduct]
    ) -> bool:
        from shopify_sdk.common.product.bulk_update import execute_bulk_product_update
        if not products or not isinstance(products, list):
            logger.warning("No products provided for bulk update.")
            return False
        
        return execute_bulk_product_update(products)
    
    def set(
        self,
        products: List[ProxyProduct]
    ) -> bool:
        from shopify_sdk.common.product.bulk.set import execute_bulk_product_set
        if not products or not isinstance(products, list):
            logger.warning("No products provided for bulk set.")
            return False
        
        return execute_bulk_product_set(products)