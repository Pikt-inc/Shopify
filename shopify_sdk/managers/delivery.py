from typing import Sequence, cast
from pydantic import BaseModel, Field, validate_call
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
    @validate_call(validate_return=True)
    def set(
        self,
        input: Sequence[tuple[ID, float]],
    ) -> bool:
        """
        Assign flat-rate delivery profiles to product variants.

        This method applies flat-rate shipping charges to the given product variants,
        using the provided sequence of (ID, rate) tuples.
        :param input: Sequence of tuples containing a product ID and its associated flat rate.
        :type input: Sequence[tuple[ID, float]]
        :return: Boolean indicating success or failure
        :rtype: bool
        """
        return self._set_shipping(input=input)

    @validate_call(validate_return=True)
    def profiles(self, merchant_only: bool = False) -> DeliveryProfileConnection:
        """
        Retrieves delivery profiles from the Shopify store.

        :param merchant_only: Flag to filter for merchant-owned profiles only.
        :type merchant_only: bool
        :return: Shopify Connection object of Delivery Profiles objects.
        :rtype: DeliveryProfileConnection
        """
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

    @validate_call(validate_return=True)
    def delete(self, id: ID) -> bool:
        """
        Deletes a delivery profile by its ID.

        :param id: ID of the delivery profile to delete.
        :type id: ID
        :return: Boolean indicating success or failure.
        :rtype: bool
        """
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

    @validate_call(validate_return=True)
    def details(self, id: ID) -> DeliveryProfile:
        """
        Retrieves detailed information about a specific delivery profile by its ID.

        :param id: ID of the delivery profile to retrieve details for.
        :type id: ID
        :return: Detailed information about the specified delivery profile.
        :rtype: DeliveryProfile
        """
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

    @validate_call(validate_return=True)
    def _bulk_create_flat_rate_shipping_profile(self, rate_prices: list[float]) -> None:
        """
        Create multiple flat-rate delivery profiles in bulk, one for each given price.

        :param rate_prices: List of flat rate prices to create shipping profiles for.
        :type rate_prices: list[float]
        :return: None
        :rtype: None
        """
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

    @validate_call(validate_return=True)
    def _get_profile_details_map(
        self, profiles: DeliveryProfileConnection
    ) -> dict[ID, DeliveryProfile]:
        """
        Generates a mapping of delivery profile IDs to their detailed DeliveryProfile objects.

        :param profiles: Shopify Connection object of Delivery Profiles objects.
        :type profiles: DeliveryProfileConnection
        :return: Mapping of profile IDs to DeliveryProfile objects.
        :rtype: dict[ID, DeliveryProfile]
        """
        profile_details_map: dict[ID, DeliveryProfile] = {}
        for node in getattr(profiles, "nodes", None) or []:
            node_id = getattr(node, "id", None)
            if not node_id:
                continue
            profile_details_map[str(node_id)] = self.details(node_id)
        return profile_details_map

    @validate_call(validate_return=True)
    def rate_to_delivery_profile(
        self,
        profile_details_map: dict[ID, DeliveryProfile],
    ) -> dict[float, ID]:
        """
        Generates a mapping of flat shipping rates to their associated delivery profile IDs.

        :param profile_details_map: Mapping of profile IDs to DeliveryProfile objects.
        :type profile_details_map: dict[ID, DeliveryProfile]
        :return: Mapping of flat shipping rates as floats to delivery profile IDs.
        :rtype: dict[float, ID]
        """
        _map: dict[float, ID] = {}
        for _dp in profile_details_map.values():
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
                        if amount in _map:
                            logger.warning(
                                "Multiple delivery profiles found for rate '%s'. Using the first one found.",
                                amount,
                            )
                            continue
                        _map[amount] = _dp.id
        return _map

    @validate_call(validate_return=True)
    def _get_profile_variant_id_map(
        self,
        profile_details_map: dict[ID, DeliveryProfile],
    ) -> dict[ID, list[ID]]:
        """
        Generates a mapping of delivery profile IDs to their associated variant IDs.

        :param profile_details_map: Mapping of profile IDs to DeliveryProfile objects.
        :type profile_details_map: dict[ID, DeliveryProfile]
        :return: Mapping of profile IDs to lists of variant IDs.
        :rtype: dict[ID, list[ID]]
        """
        profile_variant_map: dict[ID, list[ID]] = {}
        for profile in profile_details_map.values():
            variant_ids: list[ID] = []
            seen_variants: set[ID] = set()
            for profile_item in profile.profileItems.nodes:
                if (
                    not hasattr(profile_item, "variants")
                    or profile_item.variants is None
                    or not hasattr(profile_item.variants, "nodes")
                    or profile_item.variants.nodes is None
                ):
                    continue
                for variant in profile_item.variants.nodes:
                    variant_id = getattr(variant, "id", None)
                    if not variant_id:
                        continue
                    variant_id = str(variant_id)
                    if variant_id in seen_variants:
                        continue
                    seen_variants.add(variant_id)
                    variant_ids.append(variant_id)
            if variant_ids:
                profile_variant_map[str(profile.id)] = variant_ids
        return profile_variant_map

    @validate_call(validate_return=True)
    def _get_missing_rates(
        self,
        input: Sequence[tuple[ID, float]],
        rate_map: dict[float, ID],
    ) -> list[float]:
        """
        Gets a list of flat shipping rates that do not have an associated delivery profile.

        :param input: Sequence of tuples containing ID and their associated flat shipping rate.
        :type input: Sequence[tuple[ID, float]]
        :param rate_map: Mapping of rates to delivery profile IDs.
        :type rate_map: dict[float, ID]
        :return: List of float values that don't exist as a delivery profile in Shopify.
        :rtype: list[float]
        """
        missing_rates: list[float] = []
        for pid, rate in input:
            _sp_list = rate_map.get(rate)
            if not _sp_list:
                missing_rates.append(rate)
        return missing_rates

    @validate_call(validate_return=True)
    def _get_rate_to_variant_id_map(
        self,
        input: Sequence[tuple[ID, float]],
    ) -> dict[float, list[ID]]:
        """
        Generates a mapping of flat shipping rates to their associated variant IDs.

        :param input: Sequence of tuples containing product IDs and their associated flat shipping rate.
        :type input: Sequence[tuple[ID, float]]
        :return: Mapping of flat shipping rates to lists of variant IDs.
        :rtype: dict[float, list[ID]]
        """
        _variant_map = _get_store().products.bulk.product_variant_map
        rate_variant_map: dict[float, list[ID]] = {}
        for pid, rate in input:
            variant_ids = _variant_map.get(pid, [])
            if variant_ids:
                rate_variant_map.setdefault(rate, []).extend(variant_ids)
        return rate_variant_map

    @validate_call(validate_return=True)
    def _set_shipping(
        self,
        input: Sequence[tuple[ID, float]],
    ) -> bool:
        """
        Sets up shipping profiles and associates variants with the appropriate delivery profiles.

        :param input: Sequence of tuples containing product IDs and their associated flat rate.
        :type input: Sequence[tuple[ID, float]]
        :return: Boolean indicating success or failure
        :rtype: bool
        """
        profiles_connection = self.profiles(merchant_only=False)
        profile_details_map = self._get_profile_details_map(profiles_connection)
        rate_profile_map = self.rate_to_delivery_profile(profile_details_map)
        _variant_map = self._get_rate_to_variant_id_map(input=input)
        mutations: list[Mutation] = []
        missing_rates = self._get_missing_rates(input=input, rate_map=rate_profile_map)
        if missing_rates:
            self._bulk_create_flat_rate_shipping_profile(list(set(missing_rates)))
            profiles_connection = self.profiles(merchant_only=False)
            profile_details_map = self._get_profile_details_map(profiles_connection)
            rate_profile_map = self.rate_to_delivery_profile(profile_details_map)

        for pid, rate in input:
            if rate not in rate_profile_map:
                raise ValueError(
                    f"Delivery profile for rate '{rate}' was not found after creation."
                )

        profile_variant_map = self._get_profile_variant_id_map(
            profile_details_map,
        )
        for pid, rate in input:
            variant_ids = _variant_map.get(rate, [])
            profile_id = rate_profile_map.get(rate)
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
            assigned_variant_ids = set(profile_variant_map.get(str(profile_id), []))
            pending_variant_ids = [
                variant_id
                for variant_id in variant_ids
                if variant_id not in assigned_variant_ids
            ]
            if not pending_variant_ids:
                continue
            MAX_VARIANTS_PER_PROFILE_UPDATE = 250
            for i in range(
                0, len(pending_variant_ids), MAX_VARIANTS_PER_PROFILE_UPDATE
            ):
                chunk_variant_ids = pending_variant_ids[
                    i : i + MAX_VARIANTS_PER_PROFILE_UPDATE
                ]
                mutations.append(
                    deliveryProfileUpdate(
                        id=profile_id,
                        profile=DeliveryProfileInput(
                            variantsToAssociate=chunk_variant_ids
                        ),
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
