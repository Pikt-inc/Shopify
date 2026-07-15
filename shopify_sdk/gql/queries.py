from shopify_sdk.gql.versioned_proxy import VersionedGraphQLSymbol


orderByIdentifier = VersionedGraphQLSymbol("queries", "orderByIdentifier")
orders = VersionedGraphQLSymbol("queries", "orders")
products = VersionedGraphQLSymbol("queries", "products")
productVariants = VersionedGraphQLSymbol("queries", "productVariants")
publications = VersionedGraphQLSymbol("queries", "publications")
deliveryProfile = VersionedGraphQLSymbol("queries", "deliveryProfile")
deliveryProfiles = VersionedGraphQLSymbol("queries", "deliveryProfiles")
deliveryMethodDefinition = VersionedGraphQLSymbol(
    "queries", "deliveryMethodDefinition"
)
locations = VersionedGraphQLSymbol("queries", "locations")
bulkOperation = VersionedGraphQLSymbol("queries", "bulkOperation")
productSetOperation = VersionedGraphQLSymbol("queries", "productSetOperation")
productByIdentifier = VersionedGraphQLSymbol("queries", "productByIdentifier")
metafieldDefinition = VersionedGraphQLSymbol("queries", "metafieldDefinition")

__all__ = [
    "orderByIdentifier",
    "orders",
    "products",
    "productVariants",
    "publications",
    "deliveryProfile",
    "deliveryProfiles",
    "deliveryMethodDefinition",
    "locations",
    "bulkOperation",
    "productSetOperation",
    "productByIdentifier",
    "metafieldDefinition",
]
