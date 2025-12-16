from shopify_sdk.gql.queries import locations
from shopify_sdk import client
from shopify_sdk.gql.core.types.connections import *
from shopify_sdk.gql.core.types.enums import *
from shopify_sdk.gql.core.types.objects import *


def get_locations():
    location_connection: LocationConnection = locations(
        sortKey=LocationSortKeys.NAME,
        reverse=False,
    ).execute(client=client)

    if not location_connection or not location_connection.nodes:
        raise ValueError("No locations found.")

    return location_connection.nodes