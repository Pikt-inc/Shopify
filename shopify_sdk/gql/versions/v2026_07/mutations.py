from uuid import uuid4

from pydantic import BaseModel
from shopify_sdk.gql.core import Mutation
from .types.input_objects import *
from .types.payload import *
from .types.enums import OrderCancelReason, WebhookSubscriptionTopic
from typing import Iterator, Type, Dict, Set, Optional


class VersionedMutation(Mutation):
    @classmethod
    def bulk(  # type: ignore[override]
        cls, mutations: list[Mutation]
    ) -> Iterator[BaseModel]:
        """Execute mutations with this API version's bulk adapter."""
        from .bulk import bulk_mutation

        if len(mutations) == 0:
            yield from iter(())
            return
        yield from cls._build_bulk_payloads(
            mutations,
            bulk_mutation(mutations=mutations),
        )


class productUnpublish(VersionedMutation):
    return_type: Type[BaseModel] = ProductUnpublishPayload

    def __init__(
        self,
        input: ProductUnpublishInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.input: ProductUnpublishInput = input
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class productUpdate(VersionedMutation):
    return_type: Type[BaseModel] = ProductUpdatePayload

    def __init__(
        self,
        product: ProductUpdateInput,
        media: Optional[list[CreateMediaInput]] = None,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.media: Optional[list[CreateMediaInput]] = media
        self.product: ProductUpdateInput = product
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class productCreate(VersionedMutation):
    return_type: Type[BaseModel] = ProductCreatePayload

    def __init__(
        self,
        product: ProductCreateInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.product: ProductCreateInput = product
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class productDelete(VersionedMutation):
    return_type: Type[BaseModel] = ProductDeletePayload

    def __init__(
        self,
        input: ProductDeleteInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.input: ProductDeleteInput = input
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class webhookSubscriptionCreate(VersionedMutation):
    """Create an API-managed shop-scoped webhook subscription."""

    return_type: Type[BaseModel] = WebhookSubscriptionCreatePayload

    def __init__(
        self,
        topic: WebhookSubscriptionTopic,
        webhookSubscription: WebhookSubscriptionInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        """Initialize a webhook subscription create mutation."""
        self.topic: WebhookSubscriptionTopic = topic
        self.webhookSubscription: WebhookSubscriptionInput = webhookSubscription
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class webhookSubscriptionUpdate(VersionedMutation):
    """Update an API-managed shop-scoped webhook subscription."""

    return_type: Type[BaseModel] = WebhookSubscriptionUpdatePayload

    def __init__(
        self,
        id: ID,
        webhookSubscription: WebhookSubscriptionInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        """Initialize a webhook subscription update mutation."""
        self.id: ID = id
        self.webhookSubscription: WebhookSubscriptionInput = webhookSubscription
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class webhookSubscriptionDelete(VersionedMutation):
    """Delete an API-managed shop-scoped webhook subscription."""

    return_type: Type[BaseModel] = WebhookSubscriptionDeletePayload

    def __init__(
        self,
        id: ID,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        """Initialize a webhook subscription delete mutation."""
        self.id: ID = id
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class deliveryProfileUpdate(VersionedMutation):
    return_type: Type[BaseModel] = DeliveryProfileUpdatePayload

    def __init__(
        self,
        id: ID,
        profile: DeliveryProfileInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.id: ID = id
        self.profile: DeliveryProfileInput = profile
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class deliveryProfileCreate(VersionedMutation):
    return_type: Type[BaseModel] = DeliveryProfileCreatePayload

    def __init__(
        self,
        profile: DeliveryProfileInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.profile: DeliveryProfileInput = profile
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class deliveryProfileRemove(VersionedMutation):
    return_type: Type[BaseModel] = DeliveryProfileRemovePayload

    def __init__(
        self,
        id: ID,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.id: ID = id
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class productSet(VersionedMutation):
    return_type: Type[BaseModel] = ProductSetPayload

    def __init__(
        self,
        input: ProductSetInput,
        synchronous: Boolean = False,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.input: ProductSetInput = input
        self.synchronous: Boolean = synchronous
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class productPublish(VersionedMutation):
    return_type: Type[BaseModel] = ProductPublishPayload

    def __init__(
        self,
        input: ProductPublishInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.input: ProductPublishInput = input
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class productVariantsBulkUpdate(VersionedMutation):
    return_type: Type[BaseModel] = ProductVariantsBulkUpdatePayload

    def __init__(
        self,
        productId: ID,
        variants: list[ProductVariantsBulkInput],
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.productId: ID = productId
        self.variants: list[ProductVariantsBulkInput] = variants
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class productVariantsBulkCreate(VersionedMutation):
    return_type: Type[BaseModel] = ProductVariantsBulkCreatePayload

    def __init__(
        self,
        productId: ID,
        variants: list[ProductVariantsBulkInput],
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.productId: ID = productId
        self.variants: list[ProductVariantsBulkInput] = variants
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class orderUpdate(VersionedMutation):
    return_type: Type[BaseModel] = OrderUpdatePayload

    def __init__(
        self,
        input: OrderInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.input: OrderInput = input
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class orderCreate(VersionedMutation):
    return_type: Type[BaseModel] = OrderCreatePayload

    def __init__(
        self,
        order: OrderCreateOrderInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.order: OrderCreateOrderInput = order
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class orderClose(VersionedMutation):
    return_type: Type[BaseModel] = OrderClosePayload

    def __init__(
        self,
        input: OrderCloseInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.input: OrderCloseInput = input
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class orderOpen(VersionedMutation):
    return_type: Type[BaseModel] = OrderOpenPayload

    def __init__(
        self,
        input: OrderOpenInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.input: OrderOpenInput = input
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class orderMarkAsPaid(VersionedMutation):
    return_type: Type[BaseModel] = OrderMarkAsPaidPayload

    def __init__(
        self,
        input: OrderMarkAsPaidInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.input: OrderMarkAsPaidInput = input
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class orderCancel(VersionedMutation):
    return_type: Type[BaseModel] = OrderCancelPayload

    def __init__(
        self,
        orderId: ID,
        restock: Boolean,
        reason: OrderCancelReason,
        notifyCustomer: Optional[Boolean] = None,
        staffNote: Optional[String] = None,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.orderId: ID = orderId
        self.restock: Boolean = restock
        self.reason: OrderCancelReason = reason
        self.notifyCustomer: Optional[Boolean] = notifyCustomer
        self.staffNote: Optional[String] = staffNote
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class fulfillmentCreate(VersionedMutation):
    return_type: Type[BaseModel] = FulfillmentCreatePayload

    def __init__(
        self,
        fulfillment: FulfillmentInput,
        message: String = "",
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.fulfillment: FulfillmentInput = fulfillment
        self.message: String = message
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class fulfillmentCreateV2(VersionedMutation):
    return_type: Type[BaseModel] = FulfillmentCreateV2Payload

    def __init__(
        self,
        fulfillment: FulfillmentV2Input,
        message: String = "",
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.fulfillment: FulfillmentV2Input = fulfillment
        self.message: String = message
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class inventoryAdjustQuantities(VersionedMutation):
    return_type: Type[BaseModel] = InventoryAdjustQuantitiesPayload

    def __init__(
        self,
        input: InventoryAdjustQuantitiesInput,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.input: InventoryAdjustQuantitiesInput = input
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class inventorySetQuantities(VersionedMutation):
    return_type: Type[BaseModel] = InventorySetQuantitiesPayload

    def __init__(
        self,
        input: InventorySetQuantitiesInput,
        idempotency_key: Optional[String] = None,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ) -> None:
        """Initialize an idempotent absolute inventory quantity update for API version 2026-07."""
        if idempotency_key == "":
            raise ValueError("idempotency_key must not be empty.")
        self.input: InventorySetQuantitiesInput = input
        self.idempotencyKey: String = idempotency_key or str(uuid4())
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}

    @property
    def body(self) -> str:
        """Render Shopify's required idempotency directive beside the mutation field."""
        return "\n".join(
            [
                f"{self.action_type} {self.class_name}({self.arguments}) {{",
                f"{' ' * self._indent}{self.class_name}(input: $input) @idempotent(key: $idempotencyKey) {{",
                f"{self.fields}",
                f"{' ' * self._indent}}}",
                "}",
            ]
        )


class productCreateMedia(VersionedMutation):
    return_type: Type[BaseModel] = ProductCreateMediaPayload

    def __init__(
        self,
        media: list[CreateMediaInput],
        productId: ID,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.media: list[CreateMediaInput] = media
        self.productId: ID = productId
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class fileUpdate(VersionedMutation):
    return_type: Type[BaseModel] = FileUpdatePayload

    def __init__(
        self,
        files: list[FileUpdateInput],
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.files: list[FileUpdateInput] = files
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class fileDelete(VersionedMutation):
    return_type: Type[BaseModel] = FileDeletePayload

    def __init__(
        self,
        fileIds: list[ID],
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.fileIds: list[ID] = fileIds
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class stagedUploadsCreate(VersionedMutation):
    return_type: Type[BaseModel] = StagedUploadsCreatePayload

    def __init__(
        self,
        input: list[StagedUploadInput],
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.input: list[StagedUploadInput] = input
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class bulkOperationRunMutation(VersionedMutation):
    return_type: Type[BaseModel] = BulkOperationRunMutationPayload

    def __init__(
        self,
        mutation: String,
        stagedUploadPath: String,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.mutation: String = mutation
        self.stagedUploadPath: String = stagedUploadPath
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}


class bulkOperationRunQuery(VersionedMutation):
    return_type: Type[BaseModel] = BulkOperationRunQueryPayload

    def __init__(
        self,
        query: String,
        groupObjects: Boolean = True,
        field_exclusions: Optional[Dict[str, Set[str]]] = None,
        field_inclusions: Optional[Dict[str, Set[str]]] = None,
    ):
        self.query: String = query
        self.groupObjects: Boolean = groupObjects
        self._field_exclusions = field_exclusions or {}
        self._field_inclusions = field_inclusions or {}
