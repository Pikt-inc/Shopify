import logging
import time
from functools import cached_property
from typing import Iterable, Any
from .types import ProxyProduct
from shopify_sdk.tools import bulk_query
from shopify_sdk.gql import productVariants
from shopify_sdk.gql.core.types.objects import Product, ProductVariant

logger = logging.getLogger(__name__)


class ProductIdSkuResolver:
    def __init__(
        self,
        products: list[ProxyProduct],
    ):
        self._products: list[ProxyProduct] = products
        self._map: dict[str, str] = {}

    @cached_property
    def id_sku_map(self) -> dict[str, str]:
        self._build_map()
        return self._map

    @classmethod
    def from_products(
        cls,
        products: Iterable[ProxyProduct],
    ) -> "ProductIdSkuResolver":
        resolver = cls(list(products))
        resolver._resolve_products()
        return resolver

    def _get_id(self, sku: str) -> str | None:
        return self.id_sku_map.get(sku)

    def _resolve_products(self) -> None:
        for product in self._products:
            if not product.sku:
                continue
            existing_id = self._get_id(product.sku)
            if not existing_id:
                continue
            current_id = getattr(product, "id", None)
            if current_id and current_id != existing_id:
                logger.warning(
                    "SKU-based ID resolution conflict for SKU %s: existing id=%s, resolved id=%s; keeping existing id.",
                    product.sku,
                    current_id,
                    existing_id,
                )
                continue
            product.id = existing_id
        logger.info(
            f"Resolved {len(self.id_sku_map)} existing product IDs for {len(self._products)} products based on SKU."
        )

    @property
    def _query(self) -> Any:
        return productVariants(
            field_exclusions={
                "ProductVariant": ProductVariant.fields_except(
                    exclude={"sku", "product"}
                ),
                "Product": Product.fields_except(exclude={"id"}),
            },
        )

    def _build_map(self):
        start = time.perf_counter()
        target_skus = {p.sku for p in self._products if getattr(p, "sku", None)}
        if not target_skus:
            logger.info("No SKUs provided; skipping bulk productVariants lookup.")
            return
        remaining = set(target_skus)
        count = 0
        for line in bulk_query(self._query, verbose=True):
            count += 1
            product_id = line.get("product", {}).get("id")
            sku = line.get("sku")
            if not product_id or not sku or sku not in target_skus:
                continue
            existing_id = self._map.get(sku)
            if existing_id and existing_id != product_id:
                logger.warning(
                    "Conflicting product IDs for SKU %s: existing id=%s, new id=%s; keeping existing id.",
                    sku,
                    existing_id,
                    product_id,
                )
                continue
            self._map.setdefault(sku, product_id)
            if sku in remaining:
                remaining.discard(sku)
            if not remaining:
                break
        elapsed = time.perf_counter() - start
        logger.info(
            "Bulk productVariants query processed %d rows in %.3fs (resolved %d SKUs out of %d requested)",
            count,
            elapsed,
            len(target_skus) - len(remaining),
            len(target_skus),
        )
