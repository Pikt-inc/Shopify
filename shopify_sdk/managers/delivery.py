from typing import List, TYPE_CHECKING, cast
if TYPE_CHECKING:
    from shopify_sdk.gql.core.types.connections import DeliveryProfileConnection

from shopify_sdk.gql.core.types.objects import DeliveryProfile
from shopify_sdk.gql.queries import deliveryProfiles

class DeliveryManager:

    @property
    def profiles(self) -> List[DeliveryProfile]:
        query = deliveryProfiles(
            field_exclusions={
                "DeliveryProfileConnection" : {"zoneCountryCount"}
            }
        )
        from shopify_sdk.gql.core.types.connections import DeliveryProfileConnection
        response = cast(DeliveryProfileConnection, query.bulk())
        return response.nodes
