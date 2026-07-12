from types import SimpleNamespace

from shopify_sdk.common.resolver import ProductIdSkuResolver
from shopify_sdk.common.types import ProxyProduct


class FakeVariantQuery:
    def __init__(self, nodes: list[object]) -> None:
        self._nodes = nodes

    def bulk(self) -> SimpleNamespace:
        return SimpleNamespace(nodes=self._nodes)


def test_product_id_sku_resolver_updates_products_from_object_nodes(monkeypatch):
    from shopify_sdk.common import resolver as resolver_module

    calls: list[dict[str, object]] = []
    nodes = [
        SimpleNamespace(
            sku="SKU-1",
            product=SimpleNamespace(id="gid://shopify/Product/1"),
        )
    ]

    def fake_product_variants(**kwargs: object) -> FakeVariantQuery:
        calls.append(kwargs)
        return FakeVariantQuery(nodes)

    monkeypatch.setattr(resolver_module, "productVariants", fake_product_variants)
    products = [ProxyProduct(sku="SKU-1"), ProxyProduct(sku="MISSING")]

    resolver = ProductIdSkuResolver.from_products(products)

    assert products[0].id == "gid://shopify/Product/1"
    assert products[1].id is None
    assert resolver.id_sku_map == {"SKU-1": "gid://shopify/Product/1"}
    assert calls


def test_product_id_sku_resolver_supports_dictionary_nodes(monkeypatch):
    from shopify_sdk.common import resolver as resolver_module

    nodes = [{"sku": "SKU-2", "product": {"id": "gid://shopify/Product/2"}}]

    def fake_product_variants(**kwargs: object) -> FakeVariantQuery:
        return FakeVariantQuery(nodes)

    monkeypatch.setattr(resolver_module, "productVariants", fake_product_variants)
    product = ProxyProduct(sku="SKU-2")

    ProductIdSkuResolver.from_products([product])

    assert product.id == "gid://shopify/Product/2"


def test_product_id_sku_resolver_preserves_existing_conflicting_id(monkeypatch):
    from shopify_sdk.common import resolver as resolver_module

    nodes = [
        SimpleNamespace(
            sku="SKU-1",
            product=SimpleNamespace(id="gid://shopify/Product/new"),
        )
    ]

    def fake_product_variants(**kwargs: object) -> FakeVariantQuery:
        return FakeVariantQuery(nodes)

    monkeypatch.setattr(resolver_module, "productVariants", fake_product_variants)
    product = ProxyProduct(id="gid://shopify/Product/original", sku="SKU-1")

    ProductIdSkuResolver.from_products([product])

    assert product.id == "gid://shopify/Product/original"
