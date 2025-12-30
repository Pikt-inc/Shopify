import unittest
from types import SimpleNamespace
from unittest.mock import patch

from shopify_sdk.gql.core.types import OrderCreateLineItemInput
from shopify_sdk.gql.core.types.enums import OrderCancelReason
from shopify_sdk.managers.orders import OrderManager


class TestOrderManager(unittest.TestCase):
    def test_create_requires_line_items(self) -> None:
        manager = OrderManager()
        with self.assertRaises(ValueError) as ctx:
            manager.create([])

        self.assertIn("At least one line item", str(ctx.exception))

    def test_create_raises_on_user_errors(self) -> None:
        payload = SimpleNamespace(
            order=None,
            userErrors=[SimpleNamespace(message="bad")],
        )

        def fake_order_create(*args, **kwargs):
            return SimpleNamespace(execute=lambda client: payload)

        manager = OrderManager()
        line_items = [OrderCreateLineItemInput(quantity=1)]
        with patch("shopify_sdk.gql.mutations.orderCreate", new=fake_order_create):
            with self.assertRaises(ValueError) as ctx:
                manager.create(line_items=line_items)

        self.assertIn("Order creation failed", str(ctx.exception))

    def test_mark_fulfilled_raises_when_no_fulfillable_items(self) -> None:
        order = SimpleNamespace(
            fulfillmentOrders=SimpleNamespace(
                nodes=[
                    SimpleNamespace(
                        id="fo1",
                        lineItems=SimpleNamespace(
                            nodes=[
                                SimpleNamespace(id="li1", remainingQuantity=0),
                            ]
                        ),
                    )
                ]
            )
        )

        def fake_order_by_identifier(*args, **kwargs):
            return SimpleNamespace(execute=lambda client: order)

        def fake_fulfillment_create(*args, **kwargs):
            return SimpleNamespace(execute=lambda client: None)

        manager = OrderManager()
        with (
            patch("shopify_sdk.gql.orderByIdentifier", new=fake_order_by_identifier),
            patch("shopify_sdk.gql.fulfillmentCreate", new=fake_fulfillment_create),
        ):
            with self.assertRaises(ValueError) as ctx:
                manager.mark_fulfilled(
                    order_id="gid://shopify/Order/1",
                    tracking_number="1Z999",
                    tracking_company="UPS",
                )

        self.assertIn("no fulfillable line items", str(ctx.exception).lower())

    def test_mark_fulfilled_raises_on_user_errors(self) -> None:
        order = SimpleNamespace(
            fulfillmentOrders=SimpleNamespace(
                nodes=[
                    SimpleNamespace(
                        id="fo1",
                        lineItems=SimpleNamespace(
                            nodes=[
                                SimpleNamespace(id="li1", remainingQuantity=1),
                            ]
                        ),
                    )
                ]
            )
        )
        payload = SimpleNamespace(
            fulfillment=None,
            userErrors=[SimpleNamespace(message="bad")],
        )

        def fake_order_by_identifier(*args, **kwargs):
            return SimpleNamespace(execute=lambda client: order)

        def fake_fulfillment_create(*args, **kwargs):
            return SimpleNamespace(execute=lambda client: payload)

        manager = OrderManager()
        with (
            patch("shopify_sdk.gql.orderByIdentifier", new=fake_order_by_identifier),
            patch("shopify_sdk.gql.fulfillmentCreate", new=fake_fulfillment_create),
        ):
            with self.assertRaises(ValueError) as ctx:
                manager.mark_fulfilled(
                    order_id="gid://shopify/Order/1",
                    tracking_number="1Z999",
                    tracking_company="UPS",
                )

        self.assertIn("Order fulfillment failed", str(ctx.exception))

    def test_cancel_defaults_reason(self) -> None:
        calls: dict[str, object] = {}

        def fake_order_cancel(**kwargs):
            calls.update(kwargs)
            return SimpleNamespace(
                execute=lambda client: SimpleNamespace(orderCancelUserErrors=[])
            )

        manager = OrderManager()
        with (
            patch(
                "shopify_sdk.common.shipping.ensure.ensure_order_gid",
                return_value="gid://shopify/Order/1",
            ),
            patch("shopify_sdk.gql.mutations.orderCancel", new=fake_order_cancel),
        ):
            self.assertTrue(manager.cancel(order_id="1"))

        self.assertEqual(calls.get("orderId"), "gid://shopify/Order/1")
        self.assertEqual(calls.get("reason"), OrderCancelReason.OTHER)
