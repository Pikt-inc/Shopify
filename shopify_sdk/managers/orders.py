from typing import Optional, TYPE_CHECKING, cast
import datetime

if TYPE_CHECKING:
    from shopify_sdk.gql.core.types.objects import Order
    from shopify_sdk.gql.core.types.base import ID
    from shopify_sdk.gql.core.types.enums import (
        OrderDisplayFulfillmentStatus,
        OrderDisplayFinancialStatus,
    )
    from shopify_sdk.gql.core.types.enums import OrderCancelReason
    from shopify_sdk.gql.core.types.input_objects import (
        MailingAddressInput,
        OrderCreateLineItemInput,
    )
    from shopify_sdk.gql.core.types.connections import OrderConnection


class Time:
    def _utc_now(self) -> datetime.datetime:
        return datetime.datetime.now(datetime.timezone.utc)

    def _normalize(self, value: datetime.datetime) -> datetime.datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=datetime.timezone.utc)
        return value.astimezone(datetime.timezone.utc)

    def _format(self, value: datetime.datetime) -> str:
        normalized = self._normalize(value)
        return normalized.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _quote(self, value: datetime.datetime) -> str:
        return f"'{self._format(value)}'"

    def _between_constraints(
        self, start: datetime.datetime, end: datetime.datetime
    ) -> str:
        return f">={self._quote(start)} created_at:<={self._quote(end)}"

    @property
    def TODAY(self) -> str:
        now = self._utc_now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return self._between_constraints(start_of_day, now)

    @property
    def THIS_WEEK(self) -> str:
        now = self._utc_now()
        start_of_week = now - datetime.timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        return self._between_constraints(start_of_week, now)

    @property
    def THIS_MONTH(self) -> str:
        now = self._utc_now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return self._between_constraints(start_of_month, now)

    @property
    def LAST_30_DAYS(self) -> str:
        now = self._utc_now()
        past_30_days = now - datetime.timedelta(days=30)
        return self._between_constraints(past_30_days, now)

    @property
    def LAST_90_DAYS(self) -> str:
        now = self._utc_now()
        past_90_days = now - datetime.timedelta(days=90)
        return self._between_constraints(past_90_days, now)

    @property
    def LAST_180_DAYS(self) -> str:
        now = self._utc_now()
        past_180_days = now - datetime.timedelta(days=180)
        return self._between_constraints(past_180_days, now)


class OrderManager:
    Time = Time()

    @property
    def all(self) -> "OrderConnection":
        from shopify_sdk.gql.queries import orders
        from shopify_sdk.gql.core.types.connections import OrderConnection

        query = orders(
            field_inclusions={
                "Order": set(
                    {
                        "id",
                        "name",
                        "email",
                        "createdAt",
                        "totalPriceSet",
                        "financialStatus",
                        "fulfillmentStatus",
                        "shippingAddress",
                        "billingAddress",
                        "tags",
                    }
                )
            },
        )
        response = cast(OrderConnection, query.bulk())
        return response

    def query(
        self,
        fulfillment_status: Optional["OrderDisplayFulfillmentStatus"] = None,
        financial_status: Optional["OrderDisplayFinancialStatus"] = None,
        time: Optional[str] = None,
    ) -> "OrderConnection":
        from shopify_sdk.gql.queries import orders
        from shopify_sdk.gql.core.types.connections import OrderConnection

        if fulfillment_status or financial_status or time:
            query_parts = []
            if fulfillment_status:
                query_parts.append(
                    f"fulfillment_status:{fulfillment_status.value.lower()}"
                )
            if financial_status:
                query_parts.append(f"financial_status:{financial_status.value.lower()}")
            if time:
                query_parts.append(f"created_at:{time}")
            query_string = " ".join(query_parts)
        else:
            query_string = None

        query = orders(
            first=250,
            query=query_string,
            field_inclusions={
                "Order": set(
                    {
                        "id",
                        "name",
                        "email",
                        "createdAt",
                        "totalPriceSet",
                        "financialStatus",
                        "fulfillmentStatus",
                        "shippingAddress",
                        "billingAddress",
                        "tags",
                    }
                )
            },
        )
        response = cast(OrderConnection, query.bulk())
        return response

    def details(self, id: "ID") -> Optional["Order"]:
        from shopify_sdk.gql.queries import orderByIdentifier
        from shopify_sdk.gql.core.types.input_objects import OrderIdentifierInput
        from shopify_sdk import client

        identifier = OrderIdentifierInput(id=id)
        query = orderByIdentifier(
            identifier=identifier,
            field_inclusions={
                "Order": set(
                    {
                        "id",
                        "name",
                        "email",
                        "createdAt",
                        "totalPriceSet",
                        "financialStatus",
                        "fulfillmentStatus",
                        "shippingAddress",
                        "billingAddress",
                        "tags",
                        "lineItems",
                        "customer",
                        "discountApplications",
                    }
                ),
                "LineItemConnection": set({"nodes"}),
                "LineItem": set(
                    {
                        "id",
                        "sku",
                        "title",
                        "quantity",
                        "priceSet",
                        "totalDiscountSet",
                        "taxLines",
                        "product",
                    }
                ),
                "Product": set({"id"}),
            },
        )
        result: Optional["Order"] = query.execute(client)
        return result

    def create(
        self,
        line_items: list["OrderCreateLineItemInput"],
        *,
        email: Optional[str] = None,
        shipping_address: Optional["MailingAddressInput"] = None,
        note: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> "ID":
        from shopify_sdk import client
        from shopify_sdk.gql.core.types import OrderCreateOrderInput
        from shopify_sdk.gql.mutations import orderCreate

        if not line_items:
            raise ValueError("At least one line item is required to create an order.")

        input_data = OrderCreateOrderInput(
            lineItems=line_items,
            email=email,
            shippingAddress=shipping_address,
            note=note,
            tags=tags or [],
        )
        payload = orderCreate(
            order=input_data,
            field_inclusions={
                "OrderCreatePayload": {"order", "userErrors"},
                "Order": {"id"},
                "UserError": {"field", "message"},
            },
        ).execute(client)
        if payload is None:
            raise ValueError("Order creation failed; no payload returned.")
        user_errors = getattr(payload, "userErrors", []) or []
        if user_errors:
            messages = ", ".join(error.message for error in user_errors)
            raise ValueError(f"Order creation failed: {messages}")
        order = getattr(payload, "order", None)
        order_id = getattr(order, "id", None)
        if not order_id:
            raise ValueError("Order creation failed; no order returned.")
        return cast("ID", order_id)

    def close(self, order_id: "ID") -> bool:
        from shopify_sdk import client
        from shopify_sdk.common.shipping.ensure import ensure_order_gid
        from shopify_sdk.gql.core.types import OrderCloseInput
        from shopify_sdk.gql.mutations import orderClose

        order_gid = ensure_order_gid(order_id)
        payload = orderClose(
            input=OrderCloseInput(id=order_gid),
            field_inclusions={
                "OrderClosePayload": {"order", "userErrors"},
                "Order": {"id"},
                "UserError": {"field", "message"},
            },
        ).execute(client)
        if payload is None:
            raise ValueError("Order close failed; no payload returned.")
        user_errors = getattr(payload, "userErrors", []) or []
        if user_errors:
            messages = ", ".join(error.message for error in user_errors)
            raise ValueError(f"Order close failed: {messages}")
        order = getattr(payload, "order", None)
        if not getattr(order, "id", None):
            raise ValueError("Order close failed; no order returned.")
        return True

    def mark_fulfilled(
        self,
        order_id: "ID",
        *,
        tracking_number: Optional[str] = None,
        tracking_company: Optional[str] = None,
        notify_customer: bool = False,
        message: str = "",
    ) -> bool:
        from shopify_sdk import client
        from shopify_sdk.common.shipping.ensure import ensure_order_gid
        from shopify_sdk.gql import fulfillmentCreate, orderByIdentifier
        from shopify_sdk.gql.core.types import (
            FulfillmentInput,
            FulfillmentOrderLineItemInput,
            FulfillmentOrderLineItemsInput,
            FulfillmentTrackingInput,
            OrderIdentifierInput,
        )

        order_gid = ensure_order_gid(order_id)
        order = orderByIdentifier(
            identifier=OrderIdentifierInput(id=order_gid),
            field_inclusions={
                "Order": {"fulfillmentOrders"},
                "FulfillmentOrderConnection": {"nodes"},
                "FulfillmentOrder": {"id", "lineItems"},
                "FulfillmentOrderLineItemConnection": {"nodes"},
                "FulfillmentOrderLineItem": {"id", "remainingQuantity"},
            },
            connection_arguments={
                "fulfillmentOrders": {"first": 50},
                "lineItems": {"first": 250},
            },
        ).execute(client=client)
        if order is None:
            raise ValueError("Order fulfillment failed; order not found.")

        line_items_by_fulfillment: list[FulfillmentOrderLineItemsInput] = []
        fulfillment_orders = getattr(order, "fulfillmentOrders", None)
        for fulfillment_order in getattr(fulfillment_orders, "nodes", []) or []:
            items: list[FulfillmentOrderLineItemInput] = []
            fulfillment_order_id = getattr(fulfillment_order, "id", None)
            if not fulfillment_order_id:
                continue
            line_items = getattr(fulfillment_order, "lineItems", None)
            for line_item in getattr(line_items, "nodes", []) or []:
                line_item_id = getattr(line_item, "id", None)
                if not line_item_id:
                    continue
                quantity = getattr(line_item, "remainingQuantity", None)
                if quantity is None:
                    quantity = 1
                if quantity <= 0:
                    continue
                items.append(
                    FulfillmentOrderLineItemInput(
                        id=line_item_id, quantity=int(quantity)
                    )
                )
            if items:
                line_items_by_fulfillment.append(
                    FulfillmentOrderLineItemsInput(
                        fulfillmentOrderId=fulfillment_order_id,
                        fulfillmentOrderLineItems=items,
                    )
                )

        if not line_items_by_fulfillment:
            raise ValueError("Order fulfillment failed; no fulfillable line items.")

        tracking_info = None
        if tracking_number or tracking_company:
            if not tracking_number or not tracking_company:
                raise ValueError(
                    "tracking_number and tracking_company must be provided together."
                )
            tracking_info = FulfillmentTrackingInput(
                company=tracking_company,
                number=tracking_number,
            )

        fulfillment_input = FulfillmentInput(
            lineItemsByFulfillmentOrder=line_items_by_fulfillment,
            notifyCustomer=notify_customer,
            trackingInfo=tracking_info,
        )
        payload = fulfillmentCreate(
            fulfillment=fulfillment_input,
            message=message,
            field_inclusions={
                "FulfillmentCreatePayload": {"fulfillment", "userErrors"},
                "Fulfillment": {"id"},
                "UserError": {"field", "message"},
            },
        ).execute(client=client)
        if payload is None:
            raise ValueError("Order fulfillment failed; no payload returned.")
        user_errors = getattr(payload, "userErrors", []) or []
        if user_errors:
            messages = ", ".join(error.message for error in user_errors)
            raise ValueError(f"Order fulfillment failed: {messages}")
        fulfillment = getattr(payload, "fulfillment", None)
        if not getattr(fulfillment, "id", None):
            raise ValueError("Order fulfillment failed; no fulfillment returned.")
        return True

    def cancel(
        self,
        order_id: "ID",
        *,
        reason: Optional["OrderCancelReason"] = None,
        restock: bool = False,
        notify_customer: Optional[bool] = None,
        staff_note: Optional[str] = None,
    ) -> bool:
        from shopify_sdk import client
        from shopify_sdk.common.shipping.ensure import ensure_order_gid
        from shopify_sdk.gql.core.types.enums import OrderCancelReason
        from shopify_sdk.gql.mutations import orderCancel

        if reason is None:
            reason = OrderCancelReason.OTHER

        order_gid = ensure_order_gid(order_id)
        payload = orderCancel(
            orderId=order_gid,
            restock=restock,
            reason=reason,
            notifyCustomer=notify_customer,
            staffNote=staff_note,
            field_inclusions={
                "OrderCancelPayload": {"job", "orderCancelUserErrors"},
                "Job": {"id", "done"},
                "OrderCancelUserError": {"code", "field", "message"},
            },
        ).execute(client)
        if payload is None:
            raise ValueError("Order cancel failed; no payload returned.")
        cancel_errors = getattr(payload, "orderCancelUserErrors", []) or []
        if cancel_errors:
            messages = ", ".join(error.message for error in cancel_errors)
            raise ValueError(f"Order cancel failed: {messages}")
        return True
