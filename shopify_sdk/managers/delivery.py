from typing import Sequence, TYPE_CHECKING, cast
import logging

from shopify_sdk.gql.core.types.base import ID
from shopify_sdk.gql.core.types.objects import DeliveryProfile
from shopify_sdk.gql.queries import deliveryProfiles
from shopify_sdk.gql.core.types import CountryCode

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from shopify_sdk.gql.core.types.connections import DeliveryProfileConnection


class BulkDeliveryManager:
    def assign_products(
        self,
        profile_id: ID,
        product_ids: Sequence[ID],
        *,
        chunk_size: int = 250,
    ) -> list[ID]:
        from shopify_sdk import client
        from shopify_sdk.gql.core.mutation import Mutation
        from shopify_sdk.gql.core.types import (
            DeliveryProfileInput,
            ProductIdentifierInput,
        )
        from shopify_sdk.gql.mutations import deliveryProfileUpdate
        from shopify_sdk.gql.queries import productByIdentifier

        if not product_ids:
            return []

        variant_ids: list[ID] = []
        for product_id in product_ids:
            product = productByIdentifier(
                identifier=ProductIdentifierInput(id=product_id, handle=None),
                field_inclusions={
                    "Product": {"variants"},
                    "ProductVariantConnection": {"nodes"},
                    "ProductVariant": {"id"},
                },
            ).execute(client)
            if not product:
                raise ValueError(f"Product with ID '{product_id}' not found.")
            variants = product.variants.nodes if product.variants else []
            if not variants:
                raise ValueError(f"No variants found for product '{product_id}'.")
            for variant in variants:
                variant_id = getattr(variant, "id", None)
                if variant_id:
                    variant_ids.append(variant_id)

        chunks = [
            variant_ids[i : i + chunk_size]
            for i in range(0, len(variant_ids), chunk_size)
        ]
        mutations: list[Mutation] = []
        for chunk in chunks:
            mutations.append(
                deliveryProfileUpdate(
                    id=profile_id,
                    profile=DeliveryProfileInput(variantsToAssociate=chunk),
                    field_inclusions={
                        "DeliveryProfileUpdatePayload": {"profile", "userErrors"},
                        "DeliveryProfile": {"id"},
                        "UserError": {"field", "message"},
                    },
                )
            )
        for index, payload in enumerate(deliveryProfileUpdate.bulk(mutations), start=1):
            if payload is None:
                raise ValueError(
                    f"Delivery profile assignment failed; no payload returned for chunk {index}."
                )
            user_errors = getattr(payload, "userErrors", []) or []
            if user_errors:
                messages = ", ".join(error.message for error in user_errors)
                logger.error(
                    "Delivery profile assignment failed %s in bulk operation at chunk %s.",
                    messages,
                    index,
                )
                raise ValueError(
                    f"Delivery profile assignment failed {messages} in bulk operation at chunk {index}."
                )

        return list(product_ids)


class DeliveryManager:
    def __init__(self) -> None:
        self.bulk = BulkDeliveryManager()

    def profile_by_name(self, name: str) -> DeliveryProfile | None:
        profiles = self.profiles
        for profile in profiles.nodes:
            if profile.name == name:
                return profile
        return None

    def create_profile(
        self,
        name: str,
        location_ids: Sequence[ID],
        *,
        country_code: "CountryCode" = CountryCode.US,
        currency_code: str = "USD",
        rate_name: str = "Standard",
        rate_price: str = "0.00",
        zone_name: str = "Default",
    ) -> ID:
        from shopify_sdk import client
        from shopify_sdk.gql.core.types import (
            DeliveryCountryInput,
            DeliveryLocationGroupZoneInput,
            DeliveryMethodDefinitionInput,
            DeliveryProfileInput,
            DeliveryProfileLocationGroupInput,
            DeliveryRateDefinitionInput,
            MoneyInput,
        )
        from shopify_sdk.gql.mutations import deliveryProfileCreate

        profile_input = DeliveryProfileInput(
            name=name,
            locationGroupsToCreate=[
                DeliveryProfileLocationGroupInput(
                    locations=list(location_ids),
                    zonesToCreate=[
                        DeliveryLocationGroupZoneInput(
                            name=zone_name,
                            countries=[
                                DeliveryCountryInput(
                                    code=country_code,
                                    includeAllProvinces=True,
                                )
                            ],
                            methodDefinitionsToCreate=[
                                DeliveryMethodDefinitionInput(
                                    name=rate_name,
                                    active=True,
                                    rateDefinition=DeliveryRateDefinitionInput(
                                        price=MoneyInput(
                                            amount=rate_price,
                                            currencyCode=currency_code,
                                        )
                                    ),
                                )
                            ],
                        )
                    ],
                )
            ],
        )

        payload = deliveryProfileCreate(
            profile=profile_input,
            field_inclusions={
                "DeliveryProfileCreatePayload": {"profile", "userErrors"},
                "DeliveryProfile": {"id", "name"},
                "UserError": {"field", "message"},
            },
        ).execute(client)
        if payload is None:
            raise ValueError("Delivery profile creation failed; no payload returned.")
        user_errors = getattr(payload, "userErrors", []) or []
        if user_errors:
            messages = ", ".join(error.message for error in user_errors)
            raise ValueError(f"Delivery profile creation failed: {messages}")
        profile = getattr(payload, "profile", None)
        profile_id = getattr(profile, "id", None)
        if not profile_id:
            raise ValueError(
                "Delivery profile creation failed; no profile id returned."
            )
        return cast(ID, profile_id)

    def delete_profile(self, profile_id: ID) -> bool:
        from shopify_sdk import client
        from shopify_sdk.gql.mutations import deliveryProfileRemove

        payload = deliveryProfileRemove(
            id=profile_id,
            field_inclusions={
                "DeliveryProfileRemovePayload": {"job", "userErrors"},
                "Job": {"id", "done"},
                "UserError": {"field", "message"},
            },
        ).execute(client)
        if payload is None:
            raise ValueError("Delivery profile deletion failed; no payload returned.")
        user_errors = getattr(payload, "userErrors", []) or []
        if user_errors:
            messages = ", ".join(error.message for error in user_errors)
            raise ValueError(f"Delivery profile deletion failed: {messages}")
        return True

    @property
    def profiles(self) -> "DeliveryProfileConnection":
        query = deliveryProfiles(
            field_exclusions={"DeliveryProfileConnection": {"zoneCountryCount"}}
        )
        from shopify_sdk.gql.core.types.connections import DeliveryProfileConnection

        response = cast(DeliveryProfileConnection, query.bulk())
        return response

    def assign_products(self, profile_id: ID, product_ids: Sequence[ID]) -> list[ID]:
        from shopify_sdk import client
        from shopify_sdk.gql.core.types import (
            DeliveryProfileInput,
            ProductIdentifierInput,
        )
        from shopify_sdk.gql.mutations import deliveryProfileUpdate
        from shopify_sdk.gql.queries import productByIdentifier

        if not product_ids:
            return []

        variant_ids: list[ID] = []
        for product_id in product_ids:
            product = productByIdentifier(
                identifier=ProductIdentifierInput(id=product_id, handle=None),
                field_inclusions={
                    "Product": {"variants"},
                    "ProductVariantConnection": {"nodes"},
                    "ProductVariant": {"id"},
                },
            ).execute(client)
            variants = getattr(getattr(product, "variants", None), "nodes", None) or []
            if not variants:
                raise ValueError(f"No variants found for product '{product_id}'.")
            for variant in variants:
                variant_id = getattr(variant, "id", None)
                if variant_id:
                    variant_ids.append(variant_id)

        payload = deliveryProfileUpdate(
            id=profile_id,
            profile=DeliveryProfileInput(variantsToAssociate=variant_ids),
            field_inclusions={
                "DeliveryProfileUpdatePayload": {"profile", "userErrors"},
                "DeliveryProfile": {"id"},
                "UserError": {"field", "message"},
            },
        ).execute(client)
        if payload is None:
            raise ValueError("Delivery profile assignment failed; no payload returned.")
        user_errors = getattr(payload, "userErrors", []) or []
        if user_errors:
            messages = ", ".join(error.message for error in user_errors)
            raise ValueError(f"Delivery profile assignment failed: {messages}")
        return list(product_ids)
