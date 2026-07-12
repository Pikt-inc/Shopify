from types import SimpleNamespace

import pytest

from shopify_sdk.common import actions as actions_module
from shopify_sdk.common.actions import _calculate_inventory_delta
from shopify_sdk.common.actions import ProductCreate
from shopify_sdk.common.actions import ProductUpdate
from shopify_sdk.common.actions import create_product
from shopify_sdk.common.actions import update_product
from shopify_sdk.common.proxy_product_service import ProductCreateWorkflow
from shopify_sdk.common.proxy_product_service import ProductUpdateWorkflow
from shopify_sdk.common.types import ProxyProduct
from shopify_sdk.gql.core.types.input_objects import ProductCreateInput
from shopify_sdk.gql.core.types.input_objects import ProductUpdateInput


class FakeConnection:
    def __init__(self, nodes: list[object]) -> None:
        self.nodes = nodes
        self.count = len(nodes)

    @property
    def first(self) -> object | None:
        return self.nodes[0] if self.nodes else None

    def __iter__(self):
        return iter(self.nodes)


def _variant(current_quantity: int = 2) -> SimpleNamespace:
    return SimpleNamespace(
        id="gid://shopify/ProductVariant/1",
        inventoryQuantity=current_quantity,
        inventoryItem=SimpleNamespace(id="gid://shopify/InventoryItem/1"),
    )


def _location() -> SimpleNamespace:
    return SimpleNamespace(
        id="gid://shopify/Location/1",
        name="Shop location",
    )


def _proxy_product(**overrides: object) -> ProxyProduct:
    data = {
        "sku": "SKU-1",
        "title": "Example",
        "description_html": "Description",
        "vendor": "Vendor",
        "type": "Type",
        "tags": ["tag"],
        "price": "12.34",
        "seo_title": "SEO title",
        "seo_description": "SEO description",
        "quantity": 5,
        "images": ["https://example.test/image.jpg"],
    }
    data.update(overrides)
    return ProxyProduct(**data)


def test_calculate_inventory_delta_handles_missing_desired_quantity() -> None:
    assert _calculate_inventory_delta(None, 10) == 0
    assert _calculate_inventory_delta(7, 2) == 5
    assert _calculate_inventory_delta(7, None) == 7


def test_legacy_action_class_names_are_preserved() -> None:
    assert ProductCreate.__name__ == "ProductCreate"
    assert ProductUpdate.__name__ == "ProductUpdate"


def test_create_product_public_wrapper_delegates_to_create_workflow(monkeypatch):
    calls = []

    class FakeProductCreate:
        @classmethod
        def execute(cls, proxy_product):
            calls.append(proxy_product)
            return SimpleNamespace(product_id="gid://shopify/Product/1")

    product = _proxy_product()
    monkeypatch.setattr(actions_module, "ProductCreate", FakeProductCreate)

    assert create_product(product) == "gid://shopify/Product/1"
    assert calls == [product]


def test_update_product_public_wrapper_delegates_to_update_workflow(monkeypatch):
    calls = []

    class FakeProductUpdate:
        @classmethod
        def execute(cls, proxy_product):
            calls.append(proxy_product)
            return SimpleNamespace(product_id="gid://shopify/Product/1")

    product = _proxy_product(id="gid://shopify/Product/1")
    monkeypatch.setattr(actions_module, "ProductUpdate", FakeProductUpdate)

    assert update_product(product) == "gid://shopify/Product/1"
    assert calls == [product]


def test_create_product_workflow_applies_variant_inventory_images_and_publish(
    monkeypatch,
) -> None:
    from shopify_sdk.common import proxy_product_service as service_module

    calls: dict[str, object] = {}

    monkeypatch.setattr(
        service_module,
        "create_product_mutation",
        lambda input: calls.setdefault("create_input", input)
        and "gid://shopify/Product/1",
    )
    monkeypatch.setattr(
        service_module,
        "variants_by_product",
        lambda product_id: FakeConnection([_variant(current_quantity=2)]),
    )
    monkeypatch.setattr(
        service_module,
        "get_locations",
        lambda: FakeConnection([_location()]),
    )
    monkeypatch.setattr(
        service_module,
        "update_variant",
        lambda **kwargs: calls.setdefault("variant_kwargs", kwargs) or True,
    )
    monkeypatch.setattr(
        service_module,
        "update_inventory",
        lambda input: calls.setdefault("inventory_input", input) or True,
    )
    monkeypatch.setattr(
        service_module,
        "set_product_images",
        lambda product_id, images: calls.setdefault(
            "images", (product_id, images)
        )
        or True,
    )
    monkeypatch.setattr(
        service_module,
        "publish_product_to_all_publications",
        lambda product_id: calls.setdefault("published", product_id),
    )

    workflow = ProductCreateWorkflow.execute(_proxy_product(quantity=5))

    assert workflow.product_id == "gid://shopify/Product/1"
    assert isinstance(calls["create_input"], ProductCreateInput)
    assert calls["published"] == "gid://shopify/Product/1"
    assert calls["images"] == (
        "gid://shopify/Product/1",
        ["https://example.test/image.jpg"],
    )
    inventory_input = calls["inventory_input"]
    assert inventory_input.changes[0].delta == 3
    assert inventory_input.changes[0].locationId == "gid://shopify/Location/1"


def test_update_product_workflow_updates_product_and_preserves_proxy_id(
    monkeypatch,
) -> None:
    from shopify_sdk.common import proxy_product_service as service_module

    calls: dict[str, object] = {}

    monkeypatch.setattr(
        service_module,
        "update_product_mutation",
        lambda input: calls.setdefault("update_input", input)
        and "gid://shopify/Product/updated",
    )
    monkeypatch.setattr(
        service_module,
        "variants_by_product",
        lambda product_id: FakeConnection([_variant(current_quantity=5)]),
    )
    monkeypatch.setattr(
        service_module,
        "update_variant",
        lambda **kwargs: calls.setdefault("variant_kwargs", kwargs) or True,
    )
    monkeypatch.setattr(
        service_module,
        "update_inventory",
        lambda input: calls.setdefault("inventory_input", input) or True,
    )
    monkeypatch.setattr(
        service_module,
        "set_product_images",
        lambda product_id, images: calls.setdefault(
            "images", (product_id, images)
        )
        or True,
    )
    monkeypatch.setattr(
        service_module,
        "publish_product_to_all_publications",
        lambda product_id: calls.setdefault("published", product_id),
    )

    product = _proxy_product(id="gid://shopify/Product/original", quantity=5)
    workflow = ProductUpdateWorkflow.execute(product)

    assert workflow.product_id == "gid://shopify/Product/original"
    assert product.id == "gid://shopify/Product/updated"
    assert isinstance(calls["update_input"], ProductUpdateInput)
    assert calls["published"] == "gid://shopify/Product/original"
    assert "inventory_input" not in calls


def test_update_product_workflow_requires_existing_product_id() -> None:
    with pytest.raises(ValueError, match="Product ID is required"):
        ProductUpdateWorkflow.execute(_proxy_product(id=None))
