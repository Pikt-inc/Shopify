from typing import Sequence, Optional, cast
from pydantic import BaseModel, Field
import logging

from shopify_sdk.gql.core.types.base import ID
from shopify_sdk.gql.core.types.objects import DeliveryProfile
from shopify_sdk.gql.queries import deliveryProfiles
from shopify_sdk.gql.mutations import deliveryProfileCreate, deliveryProfileUpdate
from shopify_sdk.gql.core.types.connections import (
    DeliveryProfileConnection,
)
from shopify_sdk.gql.core.types.enums import CountryCode
from shopify_sdk.gql.core.types.input_objects import (
    DeliveryProfileLocationGroupInput,
    DeliveryLocationGroupZoneInput,
    DeliveryCountryInput,
    DeliveryMethodDefinitionInput,
    DeliveryRateDefinitionInput,
    MoneyInput,
    DeliveryProfileInput,
)
from shopify_sdk.gql.queries import deliveryProfile
from shopify_sdk.gql.core.types.objects import DeliveryRateDefinition
from shopify_sdk.gql.core.mutation import Mutation
from shopify_sdk import client


def _get_store():
    from shopify_sdk import store

    return store


logger = logging.getLogger(__name__)


class DeliveryProfileManager(BaseModel):
    def set(
        self,
        input: Sequence[tuple[ID, float]],
    ) -> bool:
        """
        Assign flat-rate delivery profiles to the variants for the given products.

        Args:
            entries: Sequence of ``(product_id, flat_rate)`` tuples to apply.
        """
        return self._set_shipping(input=input)

    def profiles(self, merchant_only: bool = False) -> DeliveryProfileConnection:
        query = deliveryProfiles(
            merchantOwnedOnly=merchant_only,
            field_inclusions={
                "DeliveryProfile": DeliveryProfile.fields_except(
                    [
                        "profileItems",
                        "sellingPlanGroups",
                        "profileLocationGroups",
                        "unassignedLocationsPaginated",
                        "unassignedLocations",
                    ]
                )
            },
        )

        response = cast(DeliveryProfileConnection, query.bulk())
        return response

    def delete(self, id: ID) -> bool:
        from shopify_sdk import client
        from shopify_sdk.gql.mutations import deliveryProfileRemove

        payload = deliveryProfileRemove(
            id=id,
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

    def details(self, id: ID) -> DeliveryProfile:
        query = deliveryProfile(
            id=id,
            field_inclusions={
                "DeliveryProfile": DeliveryProfile.fields_except(
                    ["sellingPlanGroups", "unassignedLocationsPaginated"]
                ),
                "DeliveryProfileItemConnection": {"nodes"},
                "Product": {"id"},
                "ProductVariantConnection": {"nodes"},
                "ProductVariant": {"id"},
                "DeliveryProfileLocationGroup": {
                    "locationGroupZones",
                },
                "DeliveryLocationGroupZoneConnection": {"nodes"},
                "DeliveryLocationGroupZone": {"methodDefinitions"},
                "DeliveryMethodDefinitionConnection": {"nodes"},
            },
        )
        profile = query.execute(client)
        if profile is None:
            raise ValueError(f"Delivery profile with ID '{id}' not found.")
        return cast(DeliveryProfile, profile)

    def _bulk_create_flat_rate_shipping_profile(self, rate_prices: list[float]) -> None:
        mutations: list[Mutation] = []
        _location_ids = _get_store().location_ids
        for rate_price in rate_prices:
            rate_price = float(rate_price)
            profile_name = f"Flat Rate ${rate_price}"
            profile_input = DeliveryProfileInput(
                name=profile_name,
                locationGroupsToCreate=[
                    DeliveryProfileLocationGroupInput(
                        locations=list(_location_ids),
                        zonesToCreate=[
                            DeliveryLocationGroupZoneInput(
                                name="Default",
                                countries=[
                                    DeliveryCountryInput(
                                        code=CountryCode.US,
                                        includeAllProvinces=True,
                                    )
                                ],
                                methodDefinitionsToCreate=[
                                    DeliveryMethodDefinitionInput(
                                        name=profile_name,
                                        active=True,
                                        rateDefinition=DeliveryRateDefinitionInput(
                                            price=MoneyInput(
                                                amount=str(rate_price),
                                                currencyCode="USD",
                                            )
                                        ),
                                    )
                                ],
                            )
                        ],
                    )
                ],
            )
            mutations.append(
                deliveryProfileCreate(
                    profile=profile_input,
                    field_inclusions={
                        "DeliveryProfileCreatePayload": {"profile", "userErrors"},
                        "DeliveryProfile": {"id", "name"},
                        "UserError": {"field", "message"},
                    },
                )
            )
        for index, payload in enumerate(deliveryProfileCreate.bulk(mutations)):
            if payload is None:
                raise ValueError(
                    f"Delivery profile creation failed; no payload returned for chunk {index}."
                )
            user_errors = getattr(payload, "userErrors", []) or []
            if user_errors:
                messages = ", ".join(error.message for error in user_errors)
                logger.error(
                    "Delivery profile creation failed %s in bulk operation at chunk %s.",
                    messages,
                    index,
                )
                raise ValueError(
                    f"Delivery profile creation failed {messages} in bulk operation at chunk {index}."
                )

    def _query(
        self,
        connection: Optional[DeliveryProfileConnection] = None,
        name: Optional[str] = None,
        flat_rate: Optional[float] = None,
    ) -> list[DeliveryProfile]:
        connection = connection or self.profiles(merchant_only=False)
        flat_rate_value = float(flat_rate) if flat_rate is not None else None
        matches: list[DeliveryProfile] = []
        for _node in connection.nodes:
            _dp = self.details(_node.id)
            for _lg in _dp.profileLocationGroups:
                for _dlg in _lg.locationGroupZones.nodes:
                    for _md in _dlg.methodDefinitions.nodes:
                        if _md.methodConditions or not _md.active:
                            continue  # implement condition checking later
                        if not isinstance(_md.rateProvider, DeliveryRateDefinition):
                            continue
                        if not hasattr(_md.rateProvider.price, "amount"):
                            continue
                        amount = float(_md.rateProvider.price.amount)
                        if name and name != _dp.name:
                            continue
                        if flat_rate_value is not None and flat_rate_value != amount:
                            continue
                        matches.append(_dp)
        return matches

    def _get_missing_rates(
        self,
        input: Sequence[tuple[ID, float]],
    ) -> list[float]:
        profiles = self.profiles(merchant_only=False)
        missing_rates: list[float] = []
        for pid, rate in input:
            _sp_list = self._query(
                connection=profiles,
                flat_rate=rate,
            )
            if not _sp_list:
                missing_rates.append(rate)
        return missing_rates

    def _get_rate_to_profile_id_map(
        self,
        input: Sequence[tuple[ID, float]],
    ) -> dict[float, ID]:
        profiles = self.profiles(merchant_only=False)
        rate_id_map: dict[float, ID] = {}
        for pid, rate in input:
            _sp_list = self._query(
                connection=profiles,
                flat_rate=rate,
            )
            if _sp_list:
                profile_id = _sp_list[0].id
                rate_id_map[rate] = profile_id
        return rate_id_map

    def _get_rate_to_variant_id_map(
        self,
        input: Sequence[tuple[ID, float]],
    ) -> dict[float, list[ID]]:
        _variant_map = _get_store().products.bulk.product_variant_map
        rate_variant_map: dict[float, list[ID]] = {}
        for pid, rate in input:
            variant_ids = _variant_map.get(pid, [])
            if variant_ids:
                rate_variant_map.setdefault(rate, []).extend(variant_ids)
        return rate_variant_map

    def _set_shipping(
        self,
        input: Sequence[tuple[ID, float]],
    ) -> bool:
        _variant_map: dict[float, list[ID]] = self._get_rate_to_variant_id_map(
            input=input
        )
        mutations: list[Mutation] = []
        missing_rates: list[float] = self._get_missing_rates(input=input)
        self._bulk_create_flat_rate_shipping_profile(list(set(missing_rates)))
        rate_profile_id_map: dict[float, ID] = self._get_rate_to_profile_id_map(
            input=input
        )

        for pid, rate in input:
            if rate not in rate_profile_id_map:
                raise ValueError(
                    f"Delivery profile for rate '{rate}' was not found after creation."
                )

        for pid, rate in input:
            variant_ids = _variant_map.get(rate, [])
            profile_id = rate_profile_id_map.get(rate)
            if not profile_id:
                logger.warning(
                    "No delivery profile found for rate '%s' during shipping profile setup.",
                    rate,
                )
                continue
            if not variant_ids:
                logger.warning(
                    "No variants found for rate '%s' during shipping profile setup.",
                    rate,
                )
                continue
            mutations.append(
                deliveryProfileUpdate(
                    id=profile_id,
                    profile=DeliveryProfileInput(variantsToAssociate=variant_ids),
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

        return True


class DeliveryManager(BaseModel):
    profiles: DeliveryProfileManager = Field(default_factory=DeliveryProfileManager)
