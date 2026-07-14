from typing import Iterator, TYPE_CHECKING
from functools import cached_property

from shopify_sdk import client as default_client
from shopify_sdk.gql.core.client import ShopifyClient
from shopify_sdk.gql.core.query import Query
from shopify_sdk.gql.mutations import bulkOperationRunQuery
from shopify_sdk.gql.core.types.payload import BulkOperationRunQueryPayload
from .models import BulkSubmissionErrorMapper
from .models import BulkSubmissionStage

MAX_JSONL_BYTES = 5 * 1024 * 1024  # 5 MB
UPLOAD_TIMEOUT_S = 300  # 5 minutes
DOWNLOAD_TIMEOUT_S = 300  # 5 minutes
POLL_INTERVAL_S = 5  # seconds

if TYPE_CHECKING:
    from shopify_sdk.gql.core.types.payload import BulkOperationResultPayload

    from .poll import BulkOperationHandle


class BulkQueryRunner:
    def __init__(
        self,
        query: Query,
        client: ShopifyClient = default_client,
        group_objects: bool = True,
    ) -> None:
        """Initialize a bulk query runner with explicit Shopify grouping behavior."""
        if not isinstance(group_objects, bool):
            raise TypeError("group_objects must be a boolean.")
        self._query: Query = query
        self._client: ShopifyClient = client
        self._group_objects = group_objects

    @cached_property
    def query(self) -> str:
        return self._query.inline_body()

    @cached_property
    def operation_id(self) -> str:
        payload: BulkOperationRunQueryPayload = bulkOperationRunQuery(
            query=self.query,
            groupObjects=self._group_objects,
        ).execute(client=self._client)
        if payload is None:
            raise ValueError("bulkOperationRunQuery returned no payload.")
        if payload.userErrors:
            raise BulkSubmissionErrorMapper.from_bulk_operation_errors(
                stage=BulkSubmissionStage.BULK_QUERY,
                errors=payload.userErrors,
            )

        if not payload.bulkOperation:
            raise ValueError("bulkOperationRunQuery returned no bulk operation.")

        return payload.bulkOperation.id

    @property
    def handle(self) -> "BulkOperationHandle":
        """Return a resumable handle for the submitted bulk query operation."""
        from .poll import BulkOperationHandle

        return BulkOperationHandle(
            operation_id=self.operation_id,
            client=self._client,
        )

    def run(
        self,
    ) -> Iterator["BulkOperationResultPayload"]:
        """Yield legacy payloads while delegating recovery state to the bulk handle."""
        for result in self.handle.iter_results():
            yield result.payload
