from typing import Optional, TYPE_CHECKING, cast
import datetime

if TYPE_CHECKING:
    from shopify_sdk.gql.core.types.objects import Order
    from shopify_sdk.gql.core.types.base import ID
    from shopify_sdk.gql.core.types.enums import OrderDisplayFulfillmentStatus, OrderDisplayFinancialStatus
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

    def _between_constraints(self, start: datetime.datetime, end: datetime.datetime) -> str:
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
        fulfillment_status: Optional[
            "OrderDisplayFulfillmentStatus"
        ] = None,
        financial_status: Optional[
            "OrderDisplayFinancialStatus"
        ] = None,
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
                query_parts.append(
                    f"financial_status:{financial_status.value.lower()}"
                )
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
