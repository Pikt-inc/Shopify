import pytest
from pydantic import BaseModel

from shopify_sdk.managers.map import MapManager, MapManagerException
from shopify_sdk.gql.core.query import Query
from shopify_sdk.gql.core.types.connections import connection
from shopify_sdk.gql.core.types.objects import Product, ProductVariant
from shopify_sdk.gql.versions.v2025_10.types.objects import Product as Product202510


class DummyModel(BaseModel):
    id: str
    handle: str
    nested: dict | None = None


class DummyConnection(connection):
    edges: list
    nodes: list[DummyModel]


class DummyQuery(Query):
    return_type = DummyConnection
    next_nodes: list[DummyModel] = []
    last_field_inclusions = None

    def __init__(self, field_inclusions=None):
        super().__init__(field_inclusions=field_inclusions)
        self._nodes = list(self.__class__.next_nodes)

    def bulk(self):
        # record the inclusions used when the query was built
        self.__class__.last_field_inclusions = self._field_inclusions
        return DummyConnection(edges=[], nodes=self._nodes)


def test_get_builds_map_from_flat_fields():
    DummyQuery.next_nodes = [
        DummyModel(id="gid://shopify/ProductVariant/1", handle="h1"),
        DummyModel(id="gid://shopify/ProductVariant/2", handle="h2"),
    ]
    DummyQuery.last_field_inclusions = None

    mgr = MapManager()
    result = mgr.get(DummyModel, "handle", "id")

    assert result == {
        "h1": "gid://shopify/ProductVariant/1",
        "h2": "gid://shopify/ProductVariant/2",
    }
    assert DummyQuery.last_field_inclusions == {
        "DummyModel": {"handle", "id"},
    }


def test_get_supports_nested_dict_path():
    DummyQuery.next_nodes = [
        DummyModel(id="id-1", handle="h1", nested={"inner": "sku-1"}),
    ]
    DummyQuery.last_field_inclusions = None

    mgr = MapManager()
    result = mgr.get(DummyModel, "nested.inner", "id")

    assert result == {"sku-1": "id-1"}


def test_get_returns_empty_when_no_nodes():
    DummyQuery.next_nodes = []
    DummyQuery.last_field_inclusions = None

    mgr = MapManager()
    result = mgr.get(DummyModel, "handle", "id")

    assert result == {}
    assert DummyQuery.last_field_inclusions == {
        "DummyModel": {"handle", "id"},
    }


def test_get_uses_inclusion_overrides():
    DummyQuery.next_nodes = [DummyModel(id="id-1", handle="h1")]
    DummyQuery.last_field_inclusions = None
    inclusions = {"DummyModel": {"customField"}}

    mgr = MapManager()
    mgr.get(DummyModel, "handle", "id", inclusion_overrides=inclusions)

    assert DummyQuery.last_field_inclusions is inclusions


def test_get_raises_when_query_missing():
    class UnknownModel(BaseModel):
        id: str
        code: str

    mgr = MapManager()
    with pytest.raises(MapManagerException):
        mgr.get(UnknownModel, "code", "id")


def test_get_query_class_uses_registry_for_shopify_models():
    mgr = MapManager()

    assert mgr._get_query_class(Product).__name__ == "products"
    assert mgr._get_query_class(Product202510).__name__ == "products"
    assert mgr._get_query_class(ProductVariant).__name__ == "productVariants"


def test_get_uses_registry_factory_for_default_product(monkeypatch):
    from shopify_sdk.gql import queries as query_module

    class ProductQuery:
        last_field_inclusions = None

        def __init__(self, field_inclusions=None):
            self._field_inclusions = field_inclusions

        def bulk(self):
            self.__class__.last_field_inclusions = self._field_inclusions
            return DummyConnection(
                edges=[],
                nodes=[DummyModel(id="gid://shopify/Product/1", handle="example")],
            )

    monkeypatch.setattr(query_module, "products", ProductQuery)

    result = MapManager().get(Product, "handle", "id")

    assert result == {"example": "gid://shopify/Product/1"}
    assert ProductQuery.last_field_inclusions == {"Product": {"handle", "id"}}
