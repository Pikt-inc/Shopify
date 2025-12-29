from typing import Iterator, TYPE_CHECKING
from functools import cached_property
import logging

from shopify_sdk import client as default_client
from shopify_sdk.gql.core.client import ShopifyClient
from shopify_sdk.gql.core.query import Query
from shopify_sdk.gql.mutations import bulkOperationRunQuery
from shopify_sdk.gql.core.types.payload import (
    BulkOperationRunQueryPayload
)

logger = logging.getLogger(__name__)

MAX_JSONL_BYTES = 5 * 1024 * 1024  # 5 MB
UPLOAD_TIMEOUT_S = 300  # 5 minutes
DOWNLOAD_TIMEOUT_S = 300  # 5 minutes
POLL_INTERVAL_S = 5  # seconds

if TYPE_CHECKING:
    from shopify_sdk.gql.core.types.payload import BulkOperationResultPayload


class BulkQueryRunner:

    def __init__(
        self,
        query: Query,
        client: ShopifyClient = default_client,
    ):
        self._query: Query = query
        self._client: ShopifyClient = client

    @cached_property
    def query(self) -> str:
        return self._query.inline_body()
    
    @cached_property
    def operation_id(self) -> str:
        payload: BulkOperationRunQueryPayload = bulkOperationRunQuery(
            query=self.query
        ).execute(client=self._client)
        if payload is None:
            logger.error("bulkOperationRunQuery returned no payload.", payload)
            raise ValueError("bulkOperationRunQuery returned no payload.")

        if not payload.bulkOperation:
            logger.error("bulkOperationRunQuery returned no bulk operation.", payload)
            raise ValueError("bulkOperationRunQuery returned no bulk operation.")
        
        return payload.bulkOperation.id
    
    def run(
        self,
    ) -> Iterator["BulkOperationResultPayload"]:
        from .poll import BulkActionResultManager

        for result in BulkActionResultManager.yield_results(
            bulk_operation_id=self.operation_id,
            client=self._client,
        ):
            yield result
