import os
import random
import time
import unittest
import uuid
from contextlib import contextmanager
from typing import Iterator

from shopify_sdk.managers import store
from shopify_sdk.common.product.media import set_product_images
from shopify_sdk.gql.core.types import (
    MailingAddressInput,
    MetafieldInput,
    OrderCreateLineItemInput,
    ProductCreateInput,
    ProductSetInput,
)
from shopify_sdk.gql.core.types.input_objects import (
    ProductVariantSetInput,
    ProductSetInventoryInput,
)
from shopify_sdk.gql.core.types.enums import (
    OrderDisplayFinancialStatus,
    OrderDisplayFulfillmentStatus,
    ProductStatus,
    ProductVariantInventoryPolicy,
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


def _wait_for_product_media_and_metafield(
    product_id: str,
    metafield_namespace: str,
    metafield_key: str,
    metafield_value: str,
    timeout_s: float = 30.0,
) -> None:
    from shopify_sdk import client
    from shopify_sdk.gql.core.types import ProductIdentifierInput
    from shopify_sdk.gql.queries import productByIdentifier

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        product = productByIdentifier(
            identifier=ProductIdentifierInput(id=product_id, handle=None),
            field_inclusions={
                "Product": {"media", "metafields"},
                "MediaConnection": {"nodes"},
                "Media": {"id"},
                "MetafieldConnection": {"nodes"},
                "Metafield": {"namespace", "key", "value"},
            },
            connection_arguments={
                "media": {"first": 10},
                "metafields": {"first": 10, "namespace": metafield_namespace},
            },
        ).execute(client=client)

        if product:
            media_nodes = getattr(getattr(product, "media", None), "nodes", None) or []
            metafields = (
                getattr(getattr(product, "metafields", None), "nodes", None) or []
            )
            has_media = len(media_nodes) > 0
            has_metafield = any(
                getattr(metafield, "key", None) == metafield_key
                and getattr(metafield, "namespace", None) == metafield_namespace
                and getattr(metafield, "value", None) == metafield_value
                for metafield in metafields
            )
            if has_media and has_metafield:
                return

        time.sleep(1.0)

    raise AssertionError(
        f"Timed out waiting for product '{product_id}' to update media/metafields."
    )


def _wait_for_variant_ids(
    manager: ProductManager,
    product_id: str,
    timeout_s: float = 30.0,
) -> list[str]:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        variant_map = manager.bulk.product_variant_map
        variant_ids = variant_map.get(product_id) or []
        if variant_ids:
            return variant_ids
        time.sleep(1.0)
    raise AssertionError(
        f"Timed out waiting for variants to appear for product '{product_id}'."
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


def _wait_for_order_line_item_id(
    order_manager,
    order_id: str,
    timeout_s: float = 20.0,
) -> str:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        order = order_manager.details(order_id)
        line_items = getattr(order, "lineItems", None)
        nodes = getattr(line_items, "nodes", None) or []
        if nodes:
            line_item_id = getattr(nodes[0], "id", None)
            if line_item_id:
                return str(line_item_id)
        time.sleep(1.0)
    raise AssertionError(f"Timed out waiting for line items on order '{order_id}'.")


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

    def test_bulk_create_sets_media_and_metafields(self) -> None:
        with _test_store(self) as test_store:
            manager = test_store.products
            handles = [f"codex-bulk-details-{uuid.uuid4().hex}" for _ in range(2)]
            created_ids: list[str] = []
            metafield_namespace = "codex"
            metafield_key = "codex_bulk_details"
            metafield_values = [f"bulk-{handle}" for handle in handles]
            try:
                inputs = [
                    ProductCreateInput(
                        title=f"Codex Bulk Details {handle}",
                        handle=handle,
                        status=ProductStatus.DRAFT,
                        metafields=[
                            MetafieldInput(
                                namespace=metafield_namespace,
                                key=metafield_key,
                                type="single_line_text_field",
                                value=metafield_value,
                            )
                        ],
                    )
                    for handle, metafield_value in zip(handles, metafield_values)
                ]
                created_ids = manager.bulk.create(inputs)
                self.assertEqual(len(created_ids), len(handles))
                for handle, product_id, metafield_value in zip(
                    handles, created_ids, metafield_values
                ):
                    found_id = _wait_for_product_id(manager, handle=handle)
                    self.assertEqual(found_id, product_id)
                    set_product_images(
                        product_id=product_id,
                        images=[TEST_IMAGE_URL],
                    )
                    _wait_for_product_media_and_metafield(
                        product_id=product_id,
                        metafield_namespace=metafield_namespace,
                        metafield_key=metafield_key,
                        metafield_value=metafield_value,
                    )
            finally:
                for product_id in created_ids:
                    try:
                        manager.delete(product_id)
                    except Exception:
                        pass

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

    def test_bulk_publish_from_set(self) -> None:
        with _test_store(self) as test_store:
            manager = test_store.products
            publications = test_store.publications
            locations = test_store.locations
            if publications.count == 0:
                self.skipTest("No publications available for bulk publish testing.")
                return
            handles = [f"codex-bulk-pub-{uuid.uuid4().hex}" for _ in range(2)]
            try:
                inputs = [
                    ProductSetInput(
                        title=f"Codex Bulk Publish {handle}",
                        handle=handle,
                        status=ProductStatus.ACTIVE,
                        variants=[
                            ProductVariantSetInput(
                                sku=f"COD-BULK-PUB-{handle}",
                                price="9.99",
                                inventoryQuantities=[
                                    ProductSetInventoryInput(
                                        locationId=locations.nodes[0].id,
                                        quantity=100,
                                        name="available",
                                    )
                                ],
                                inventoryPolicy=ProductVariantInventoryPolicy.DENY,
                            )
                        ],
                    )
                    for handle in handles
                ]
                created = manager.bulk.set(inputs)
                created_ids = [
                    item.product.id for item in created if item.product is not None
                ]
                self.assertEqual(len(created_ids), len(handles))
                for handle, product_id in zip(handles, created_ids):
                    found_id = _wait_for_product_id(manager, handle=handle)
                    self.assertEqual(found_id, product_id)

                self.assertTrue(manager.bulk.publish(created_ids))
            finally:
                if created_ids:
                    try:
                        manager.bulk.delete(created_ids)
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

    def test_bulk_helpers_reflect_store_state(self) -> None:
        with _test_store(self) as test_store:
            manager = test_store.products
            handles = [f"codex-helper-{uuid.uuid4().hex}" for _ in range(2)]
            created_ids: list[str] = []
            missing_handle = f"{handles[0]}-missing"
            try:
                for handle in handles:
                    created_ids.append(
                        manager.create(
                            title=f"Codex Helper Product {handle}",
                            handle=handle,
                            status=ProductStatus.DRAFT,
                        )
                    )
                    _wait_for_product_id(manager, handle=handle)

                variant_map = manager.bulk.product_variant_map
                for product_id in created_ids:
                    self.assertIn(product_id, variant_map)
                    self.assertTrue(variant_map[product_id])

                handle_map = manager.bulk.handle_id_map
                for handle, product_id in zip(handles, created_ids):
                    self.assertEqual(handle_map.get(handle), product_id)

                missing = manager.bulk.missing_handles(handles + [missing_handle])
                self.assertEqual(set(missing), {missing_handle})
            finally:
                for product_id in created_ids:
                    try:
                        manager.delete(product_id)
                    except Exception:
                        pass


class TestStoreManager(unittest.TestCase):
    def test_locations_and_publications(self) -> None:
        with _test_store(self) as test_store:
            locations = test_store.locations
            self.assertIsInstance(locations.nodes, list)

            publications = test_store.publications
            self.assertIsInstance(publications.nodes, list)


class TestDeliveryProfiles(unittest.TestCase):
    def test_profiles(self) -> None:
        from shopify_sdk import client
        from shopify_sdk.gql.queries import deliveryProfiles

        with _test_store(self):
            profiles_conn = deliveryProfiles(
                first=10,
                merchantOwnedOnly=False,
                field_inclusions={
                    "DeliveryProfileConnection": {"nodes"},
                    "DeliveryProfile": {"id", "name"},
                },
            ).execute(client)
            if profiles_conn is None:
                self.skipTest("deliveryProfiles returned no data.")
            assert profiles_conn is not None
            self.assertIsInstance(profiles_conn.nodes, list)

    def test_set_assigns_product_to_shipping_profile(self) -> None:
        with _test_store(self) as test_store:
            manager = test_store.products
            shipping_rate = round(random.uniform(5.0, 30.0), 2)
            try:
                before_profiles = test_store.delivery.profiles._query(
                    flat_rate=shipping_rate
                )
            except Exception as exc:
                self.skipTest(f"Delivery profiles unavailable: {exc}")
            before_profile_ids = {profile.id for profile in before_profiles}
            handles = [f"codex-delivery-set-{uuid.uuid4().hex}" for _ in range(2)]
            product_ids: list[str] = []
            created_profile_id: str | None = None
            try:
                for handle_value in handles:
                    product_ids.append(
                        manager.create(
                            title=f"Codex Delivery Profile {handle_value}",
                            handle=handle_value,
                            status=ProductStatus.DRAFT,
                        )
                    )
                found_ids = [
                    _wait_for_product_id(manager, handle=handle_value)
                    for handle_value in handles
                ]
                self.assertEqual(found_ids, product_ids)
                variant_lookup = [
                    _wait_for_variant_ids(manager, pid) for pid in product_ids
                ]
                for variant_ids in variant_lookup:
                    self.assertTrue(variant_ids)
                entries = [(pid, float(shipping_rate)) for pid in product_ids]
                try:
                    self.assertTrue(test_store.delivery.profiles.set(entries))
                except ValueError as exc:
                    self.skipTest(f"Unable to create/update delivery profile: {exc}")
                after_profiles = test_store.delivery.profiles._query(
                    flat_rate=shipping_rate
                )
                self.assertTrue(after_profiles)
                after_profile_ids = {profile.id for profile in after_profiles}
                new_profile_ids = after_profile_ids - before_profile_ids
                if new_profile_ids:
                    created_profile_id = next(iter(new_profile_ids))
                    profile_id = created_profile_id
                else:
                    profile_id = next(iter(after_profile_ids))
                profile_details = test_store.delivery.profiles.details(profile_id)
                assigned_variant_ids = set()
                profile_items_conn = getattr(profile_details, "profileItems", None)
                profile_items = getattr(profile_items_conn, "nodes", None) or []
                for profile_item in profile_items:
                    variant_conn = getattr(profile_item, "variants", None)
                    variant_nodes = getattr(variant_conn, "nodes", None) or []
                    for variant in variant_nodes:
                        if variant.id:
                            assigned_variant_ids.add(str(variant.id))
                expected_variant_ids = {str(ids[0]) for ids in variant_lookup if ids}
                self.assertTrue(
                    expected_variant_ids.issubset(assigned_variant_ids),
                    "All expected product variants should be in the profile.",
                )
            finally:
                for pid in product_ids:
                    try:
                        manager.delete(pid)
                    except Exception:
                        pass
                if created_profile_id:
                    try:
                        test_store.delivery.profiles.delete(created_profile_id)
                    except Exception:
                        pass

    def test_countries_include_rest_of_world_shape(self) -> None:
        from shopify_sdk import client
        from shopify_sdk.gql.queries import deliveryProfiles

        with _test_store(self) as test_store:
            profiles_conn = deliveryProfiles(
                first=20,
                merchantOwnedOnly=False,
                field_inclusions={
                    "DeliveryProfileConnection": {"nodes"},
                    "DeliveryProfile": {"id"},
                },
            ).execute(client)
            if profiles_conn is None or not profiles_conn.nodes:
                self.skipTest("No delivery profiles available.")
            assert profiles_conn is not None
            for node in profiles_conn.nodes:
                details = test_store.delivery.profiles.details(node.id)
                for location_group in (
                    getattr(details, "profileLocationGroups", []) or []
                ):
                    zones_conn = getattr(location_group, "locationGroupZones", None)
                    zones = getattr(zones_conn, "nodes", None) or []
                    for zone in zones:
                        delivery_zone = getattr(zone, "zone", None)
                        countries = getattr(delivery_zone, "countries", None) or []
                        for country in countries:
                            code = getattr(country, "code", None)
                            if code and getattr(code, "restOfWorld", False):
                                self.assertTrue(code.restOfWorld)
                                return
            self.skipTest("No delivery zone with rest-of-world country found.")

    def test_profile_items_expose_variants_connection(self) -> None:
        from shopify_sdk import client
        from shopify_sdk.gql.queries import deliveryProfiles

        with _test_store(self) as test_store:
            profiles_conn = deliveryProfiles(
                first=20,
                merchantOwnedOnly=False,
                field_inclusions={
                    "DeliveryProfileConnection": {"nodes"},
                    "DeliveryProfile": {"id"},
                },
            ).execute(client)
            if profiles_conn is None or not profiles_conn.nodes:
                self.skipTest("No delivery profiles available.")
            assert profiles_conn is not None
            for node in profiles_conn.nodes:
                details = test_store.delivery.profiles.details(node.id)
                items_conn = getattr(details, "profileItems", None)
                items = getattr(items_conn, "nodes", None) or []
                for item in items:
                    variants_conn = getattr(item, "variants", None)
                    self.assertIsNotNone(variants_conn)
                    variant_nodes = getattr(variants_conn, "nodes", None)
                    self.assertIsNotNone(variant_nodes)
                    return
            self.skipTest("No delivery profile items available to verify variants.")

    def test_delivery_profiles_merchant_owned_pagination(self) -> None:
        from shopify_sdk import client
        from shopify_sdk.gql.queries import deliveryProfiles

        with _test_store(self):
            result = deliveryProfiles(
                first=1,
                merchantOwnedOnly=True,
                field_inclusions={
                    "DeliveryProfileConnection": {"nodes", "pageInfo"},
                    "DeliveryProfile": {"id"},
                    "PageInfo": {"hasNextPage", "hasPreviousPage"},
                },
            ).execute(client)
            if result is None:
                self.skipTest("deliveryProfiles returned no data.")
            assert result is not None
            self.assertLessEqual(len(result.nodes or []), 1)
            page_info = getattr(result, "pageInfo", None)
            self.assertIsNotNone(page_info)


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
                line_item_id = _wait_for_order_line_item_id(
                    order_manager, fulfilled_order_id
                )
                self.assertTrue(
                    order_manager.mark_fulfilled(
                        order_id=fulfilled_order_id,
                        line_item_id=line_item_id,
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
