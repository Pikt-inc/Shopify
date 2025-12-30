import os
import time
import unittest
import uuid
from contextlib import contextmanager
from typing import Iterator

from shopify_sdk import store
from shopify_sdk.gql.core.types import (
    MailingAddressInput,
    MetafieldInput,
    OrderCreateLineItemInput,
    ProductCreateInput,
)
from shopify_sdk.gql.core.types.enums import (
    OrderDisplayFinancialStatus,
    OrderDisplayFulfillmentStatus,
    ProductStatus,
)
from shopify_sdk.managers.products import ProductManager
from shopify_sdk.managers.store import StoreManager

TEST_IMAGE_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/"
    "Example.jpg/640px-Example.jpg"
)
TEST_METAFIELDS = [
    MetafieldInput(
        namespace="codex",
        key="codex_test",
        type="single_line_text_field",
        value="codex",
    )
]


@contextmanager
def _test_store(testcase: unittest.TestCase) -> Iterator[StoreManager]:
    shop_domain = os.getenv("TEST_SHOPIFY_SHOP_DOMAIN")
    access_token = os.getenv("TEST_SHOPIFY_ACCESS_TOKEN")
    if not shop_domain or not access_token:
        testcase.skipTest(
            "Set TEST_SHOPIFY_SHOP_DOMAIN and TEST_SHOPIFY_ACCESS_TOKEN to use test credentials."
        )
        return
    api_version = os.getenv("TEST_SHOPIFY_API_VERSION") or os.getenv(
        "SHOPIFY_API_VERSION"
    )
    with store.credentials_context(
        shop_domain=shop_domain,
        access_token=access_token,
        api_version=api_version,
    ) as test_store:
        yield test_store


def _wait_for_product_id(
    manager: ProductManager,
    handle: str,
    timeout_s: float = 20.0,
) -> str:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        found_id = manager.find_product_id(handle=handle)
        if found_id:
            return found_id
        time.sleep(1.0)
    raise AssertionError(
        f"Timed out waiting for product handle '{handle}' to be searchable."
    )


def _wait_for_product_absence(
    manager: ProductManager,
    handle: str,
    timeout_s: float = 20.0,
) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        found_id = manager.find_product_id(handle=handle)
        if not found_id:
            return
        time.sleep(1.0)
    raise AssertionError(
        f"Timed out waiting for product handle '{handle}' to be deleted."
    )


def _wait_for_profile_absence(
    delivery_manager,
    profile_id: str,
    timeout_s: float = 30.0,
) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        profiles = delivery_manager.profiles
        if not any(profile.id == profile_id for profile in profiles.nodes):
            return
        time.sleep(1.0)
    raise AssertionError(
        f"Timed out waiting for delivery profile '{profile_id}' to be deleted."
    )


class TestProductManager(unittest.TestCase):
    def test_create_find_exchange_set_status_delete(self) -> None:
        with _test_store(self) as test_store:
            manager = test_store.products
            handle = f"codex-test-{uuid.uuid4().hex}"
            product_id = None
            try:
                product_id = manager.create(
                    title=f"Codex Test Product {handle}",
                    handle=handle,
                    status=ProductStatus.DRAFT,
                    images=[TEST_IMAGE_URL],
                    metafields=TEST_METAFIELDS,
                )

                found_id = _wait_for_product_id(manager, handle=handle)
                self.assertEqual(found_id, product_id)

                exchange_id = manager.exchange(handle=handle)
                self.assertEqual(exchange_id, product_id)

                payload = manager.set_status(
                    id=product_id,
                    status=ProductStatus.ARCHIVED,
                )
                self.assertIsNotNone(payload)
                assert payload is not None
                self.assertIsNotNone(payload.product)
                assert payload.product is not None
                self.assertEqual(payload.product.id, product_id)
                self.assertEqual(payload.product.status, ProductStatus.ARCHIVED)
                self.assertEqual(payload.userErrors, [])
            finally:
                if product_id:
                    manager.delete(product_id)

    def test_bulk_create(self) -> None:
        with _test_store(self) as test_store:
            manager = test_store.products
            handles = [f"codex-bulk-{uuid.uuid4().hex}" for _ in range(2)]
            created_ids: list[str] = []
            try:
                inputs = [
                    ProductCreateInput(
                        title=f"Codex Bulk Product {handles[0]}",
                        handle=handles[0],
                        status=ProductStatus.DRAFT,
                    ),
                    ProductCreateInput(
                        title=f"Codex Bulk Product {handles[1]}",
                        handle=handles[1],
                        status=ProductStatus.DRAFT,
                    ),
                ]
                created_ids = manager.bulk.create(inputs)
                self.assertEqual(len(created_ids), 2)
                for handle, product_id in zip(handles, created_ids):
                    found_id = _wait_for_product_id(manager, handle=handle)
                    self.assertEqual(found_id, product_id)
            finally:
                for product_id in created_ids:
                    manager.delete(product_id)

    def test_bulk_delete(self) -> None:
        with _test_store(self) as test_store:
            manager = test_store.products
            handles = [f"codex-bulk-del-{uuid.uuid4().hex}" for _ in range(2)]
            created_ids: list[str] = []
            try:
                inputs = [
                    ProductCreateInput(
                        title=f"Codex Bulk Delete Product {handles[0]}",
                        handle=handles[0],
                        status=ProductStatus.DRAFT,
                    ),
                    ProductCreateInput(
                        title=f"Codex Bulk Delete Product {handles[1]}",
                        handle=handles[1],
                        status=ProductStatus.DRAFT,
                    ),
                ]
                created_ids = manager.bulk.create(inputs)
                deleted_ids = manager.bulk.delete(created_ids)
                self.assertEqual(set(deleted_ids), set(created_ids))
                for handle in handles:
                    _wait_for_product_absence(manager, handle=handle)
            finally:
                for product_id in created_ids:
                    try:
                        manager.delete(product_id)
                    except Exception:
                        pass

    def test_lists(self) -> None:
        with _test_store(self) as test_store:
            manager = test_store.products

            active = manager.active
            self.assertIsInstance(active.nodes, list)

            archived = manager.archived
            self.assertIsInstance(archived.nodes, list)

            drafted = manager.drafted
            self.assertIsInstance(drafted.nodes, list)


class TestStoreManager(unittest.TestCase):
    def test_locations_and_publications(self) -> None:
        with _test_store(self) as test_store:
            locations = test_store.locations
            self.assertIsInstance(locations.nodes, list)

            publications = test_store.publications
            self.assertIsInstance(publications.nodes, list)


class TestDeliveryManager(unittest.TestCase):
    def test_profiles(self) -> None:
        with _test_store(self) as test_store:
            profiles = test_store.delivery.profiles
            self.assertIsInstance(profiles.nodes, list)

    def test_assign_products_to_profile(self) -> None:
        with _test_store(self) as test_store:
            delivery_manager = test_store.delivery
            locations = test_store.locations.nodes
            if not locations:
                self.skipTest("No locations available for delivery profile creation.")
                return
            profile_id = None
            profile_id = delivery_manager.create_profile(
                name=f"Codex Test Profile {uuid.uuid4().hex}",
                location_ids=[locations[0].id],
            )
            profiles = delivery_manager.profiles
            self.assertTrue(any(profile.id == profile_id for profile in profiles.nodes))

            product_manager = test_store.products
            handles = [f"codex-ship-{uuid.uuid4().hex}" for _ in range(2)]
            created_ids: list[str] = []
            try:
                for handle in handles:
                    created_ids.append(
                        product_manager.create(
                            title=f"Codex Delivery Product {handle}",
                            handle=handle,
                            status=ProductStatus.DRAFT,
                        )
                    )
                assigned_single = delivery_manager.assign_products(
                    profile_id=profile_id,
                    product_ids=[created_ids[0]],
                )
                self.assertEqual(assigned_single, [created_ids[0]])

                assigned_bulk = delivery_manager.bulk.assign_products(
                    profile_id=profile_id,
                    product_ids=created_ids[1:],
                )
                self.assertEqual(assigned_bulk, created_ids[1:])
            finally:
                if created_ids:
                    product_manager.bulk.delete(created_ids)
                if profile_id:
                    try:
                        delivery_manager.delete_profile(profile_id)
                        _wait_for_profile_absence(delivery_manager, profile_id)
                    except Exception:
                        pass


class TestOrderManager(unittest.TestCase):
    def test_query_with_filters(self) -> None:
        with _test_store(self) as test_store:
            orders = test_store.orders.query(
                fulfillment_status=OrderDisplayFulfillmentStatus.UNFULFILLED,
                financial_status=OrderDisplayFinancialStatus.PAID,
                time=test_store.orders.Time.LAST_30_DAYS,
            )
            self.assertIsNotNone(orders)
            self.assertIsInstance(orders.nodes, list)

    def test_create_fulfill_cancel_order(self) -> None:
        with _test_store(self) as test_store:
            product_manager = test_store.products
            order_manager = test_store.orders
            handle = f"codex-order-{uuid.uuid4().hex}"
            product_id = None
            fulfilled_order_id = None
            cancel_order_id = None
            try:
                product_id = product_manager.create(
                    title=f"Codex Order Product {handle}",
                    handle=handle,
                    status=ProductStatus.ACTIVE,
                )
                product_id = _wait_for_product_id(product_manager, handle=handle)
                variant_id = product_manager.first_variant_id(product_id)

                shipping_address = MailingAddressInput(
                    address1="123 Codex St",
                    address2="Suite 1",
                    city="San Francisco",
                    company="Codex",
                    countryCode="US",
                    firstName="Codex",
                    lastName="Test",
                    phone="555-555-5555",
                    provinceCode="CA",
                    zip="94105",
                )
                line_items = [
                    OrderCreateLineItemInput(variantId=variant_id, quantity=1)
                ]
                fulfilled_order_id = order_manager.create(
                    line_items=line_items,
                    email="codex-test@example.com",
                    shipping_address=shipping_address,
                    note="Codex test order",
                )
                self.assertIsNotNone(fulfilled_order_id)
                self.assertTrue(
                    order_manager.mark_fulfilled(
                        order_id=fulfilled_order_id,
                        tracking_company="UPS",
                        tracking_number="1Z999AA10023456784",
                    )
                )

                cancel_order_id = order_manager.create(
                    line_items=line_items,
                    email="codex-test-cancel@example.com",
                    shipping_address=shipping_address,
                    note="Codex test order (cancel)",
                )
                self.assertIsNotNone(cancel_order_id)
                self.assertTrue(order_manager.cancel(cancel_order_id, restock=True))
            finally:
                if cancel_order_id:
                    try:
                        order_manager.cancel(cancel_order_id, restock=True)
                    except Exception:
                        pass
                if fulfilled_order_id:
                    try:
                        order_manager.close(fulfilled_order_id)
                    except Exception:
                        pass
                if product_id:
                    try:
                        product_manager.delete(product_id)
                    except Exception:
                        pass
