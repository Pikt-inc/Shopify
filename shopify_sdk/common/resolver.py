import logging
import time
from functools import cached_property
from typing import Iterable, cast

from .types import ProxyProduct
from shopify_sdk.gql import productVariants
from shopify_sdk.gql.core.query import Query
from shopify_sdk.gql.core.types.objects import Product, ProductVariant

logger = logging.getLogger(__name__)


class ProductIdSkuResolver:
    def __init__(
        self,
        products: list[ProxyProduct],
    ) -> None:
        """Initialize the resolver for proxy products keyed by SKU.

        :param products: Proxy products to mutate with resolved Shopify IDs.
        """
        self._products: list[ProxyProduct] = products
        self._map: dict[str, str] = {}

    @cached_property
    def id_sku_map(self) -> dict[str, str]:
        """Return the SKU-to-product-ID map resolved from Shopify variants."""
        self._build_map()
        return self._map

    @classmethod
    def from_products(
        cls,
        products: Iterable[ProxyProduct],
    ) -> "ProductIdSkuResolver":
        """Build a resolver and apply resolved product IDs to the input products.

        :param products: Proxy products whose SKUs should be resolved.
        :returns: Resolver containing the SKU-to-product-ID map.
        """
        resolver = cls(list(products))
        resolver._resolve_products()
        return resolver

    def _get_id(self, sku: str) -> str | None:
        """Return the resolved Shopify product ID for a SKU, when available."""
        return self.id_sku_map.get(sku)

    def _resolve_products(self) -> None:
        """Mutate proxy products with resolved IDs while preserving conflicts."""
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
            "Resolved %d existing product IDs for %d products based on SKU.",
            len(self.id_sku_map),
            len(self._products),
        )

    @property
    def _query(self) -> Query:
        """Return the version-aware product variants query used for ID lookup."""
        return cast(
            Query,
            productVariants(
                field_exclusions={
                    "ProductVariant": ProductVariant.fields_except(
                        exclude={"sku", "product"}
                    ),
                    "Product": Product.fields_except(exclude={"id"}),
                },
            ),
        )

    def _build_map(self) -> None:
        """Populate the SKU-to-product-ID map from product variant bulk results."""
        start = time.perf_counter()
        target_skus = {str(p.sku) for p in self._products if getattr(p, "sku", None)}
        if not target_skus:
            logger.info("No SKUs provided; skipping bulk productVariants lookup.")
            return
        remaining = set(target_skus)
        count = self._populate_map(target_skus, remaining)
        self._log_bulk_summary(count, start, target_skus, remaining)

    def _populate_map(self, target_skus: set[str], remaining: set[str]) -> int:
        """Populate the map from bulk variant nodes.

        :param target_skus: SKUs requested by caller products.
        :param remaining: Mutable set of unresolved SKUs.
        :returns: Number of bulk variant rows processed.
        """
        count = 0
        for variant in self._bulk_variant_nodes():
            count += 1
            self._record_variant(variant, target_skus, remaining)
            if not remaining:
                break
        return count

    def _record_variant(
        self, variant: object, target_skus: set[str], remaining: set[str]
    ) -> None:
        """Record one variant's parent product ID when it matches a target SKU.

        :param variant: Product variant object or dictionary from bulk output.
        :param target_skus: SKUs requested by caller products.
        :param remaining: Mutable set of unresolved SKUs.
        """
        product_id = self._variant_product_id(variant)
        sku = self._variant_sku(variant)
        if not product_id or not sku or sku not in target_skus:
            return
        existing_id = self._map.get(sku)
        if existing_id and existing_id != product_id:
            logger.warning(
                "Conflicting product IDs for SKU %s: existing id=%s, new id=%s; keeping existing id.",
                sku,
                existing_id,
                product_id,
            )
            return
        self._map.setdefault(sku, product_id)
        remaining.discard(sku)

    def _log_bulk_summary(
        self, count: int, start: float, target_skus: set[str], remaining: set[str]
    ) -> None:
        """Log the SKU resolution result summary.

        :param count: Number of bulk variant rows processed.
        :param start: Start time from ``time.perf_counter``.
        :param target_skus: SKUs requested by caller products.
        :param remaining: SKUs unresolved after processing.
        """
        elapsed = time.perf_counter() - start
        logger.info(
            "Bulk productVariants query processed %d rows in %.3fs (resolved %d SKUs out of %d requested)",
            count,
            elapsed,
            len(target_skus) - len(remaining),
            len(target_skus),
        )

    def _bulk_variant_nodes(self) -> Iterable[object]:
        """Return bulk product variant nodes from the active GraphQL query."""
        connection = self._query.bulk()
        nodes = getattr(connection, "nodes", None)
        if nodes is None and isinstance(connection, dict):
            nodes = connection.get("nodes")
        return nodes or []

    def _variant_product_id(self, variant: object) -> str | None:
        """Return the parent product ID from a variant object or dictionary."""
        product = self._value(variant, "product")
        product_id = self._value(product, "id")
        return str(product_id) if product_id else None

    def _variant_sku(self, variant: object) -> str | None:
        """Return the SKU from a variant object or dictionary."""
        sku = self._value(variant, "sku")
        return str(sku) if sku else None

    def _value(self, obj: object, key: str) -> object | None:
        """Return a field value from an object or dictionary.

        :param obj: Object or dictionary containing the field.
        :param key: Field name to resolve.
        :returns: Field value when available.
        """
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key, None)
