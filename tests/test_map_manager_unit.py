import pytest
from pydantic import BaseModel

from shopify_sdk.managers.map import MapManager, MapManagerException
from shopify_sdk.gql.core.query import Query
from shopify_sdk.gql.core.types.connections import connection


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
