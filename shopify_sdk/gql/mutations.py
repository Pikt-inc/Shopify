from shopify_sdk.gql.versioned_proxy import VersionedGraphQLSymbol


productUnpublish = VersionedGraphQLSymbol("mutations", "productUnpublish")
productPublish = VersionedGraphQLSymbol("mutations", "productPublish")
productCreate = VersionedGraphQLSymbol("mutations", "productCreate")
productDelete = VersionedGraphQLSymbol("mutations", "productDelete")
metafieldDefinitionCreate = VersionedGraphQLSymbol(
    "mutations", "metafieldDefinitionCreate"
)
deliveryProfileUpdate = VersionedGraphQLSymbol("mutations", "deliveryProfileUpdate")
deliveryProfileCreate = VersionedGraphQLSymbol("mutations", "deliveryProfileCreate")
deliveryProfileRemove = VersionedGraphQLSymbol("mutations", "deliveryProfileRemove")
productVariantsBulkUpdate = VersionedGraphQLSymbol(
    "mutations", "productVariantsBulkUpdate"
)
productVariantsBulkCreate = VersionedGraphQLSymbol(
    "mutations", "productVariantsBulkCreate"
)
productUpdate = VersionedGraphQLSymbol("mutations", "productUpdate")
productSet = VersionedGraphQLSymbol("mutations", "productSet")
orderUpdate = VersionedGraphQLSymbol("mutations", "orderUpdate")
orderCreate = VersionedGraphQLSymbol("mutations", "orderCreate")
orderClose = VersionedGraphQLSymbol("mutations", "orderClose")
orderOpen = VersionedGraphQLSymbol("mutations", "orderOpen")
orderMarkAsPaid = VersionedGraphQLSymbol("mutations", "orderMarkAsPaid")
orderCancel = VersionedGraphQLSymbol("mutations", "orderCancel")
fulfillmentCreate = VersionedGraphQLSymbol("mutations", "fulfillmentCreate")
fulfillmentCreateV2 = VersionedGraphQLSymbol("mutations", "fulfillmentCreateV2")
productCreateMedia = VersionedGraphQLSymbol("mutations", "productCreateMedia")
fileUpdate = VersionedGraphQLSymbol("mutations", "fileUpdate")
fileDelete = VersionedGraphQLSymbol("mutations", "fileDelete")
stagedUploadsCreate = VersionedGraphQLSymbol("mutations", "stagedUploadsCreate")
bulkOperationRunMutation = VersionedGraphQLSymbol(
    "mutations", "bulkOperationRunMutation"
)
bulkOperationRunQuery = VersionedGraphQLSymbol("mutations", "bulkOperationRunQuery")
inventoryAdjustQuantities = VersionedGraphQLSymbol(
    "mutations", "inventoryAdjustQuantities"
)
inventorySetQuantities = VersionedGraphQLSymbol("mutations", "inventorySetQuantities")

__all__ = [
    "productUnpublish",
    "productPublish",
    "productCreate",
    "productDelete",
    "metafieldDefinitionCreate",
    "deliveryProfileUpdate",
    "deliveryProfileCreate",
    "deliveryProfileRemove",
    "productVariantsBulkUpdate",
    "productVariantsBulkCreate",
    "productUpdate",
    "productSet",
    "orderUpdate",
    "orderCreate",
    "orderClose",
    "orderOpen",
    "orderMarkAsPaid",
    "orderCancel",
    "fulfillmentCreate",
    "fulfillmentCreateV2",
    "productCreateMedia",
    "fileUpdate",
    "fileDelete",
    "stagedUploadsCreate",
    "bulkOperationRunMutation",
    "bulkOperationRunQuery",
    "inventoryAdjustQuantities",
    "inventorySetQuantities",
]
