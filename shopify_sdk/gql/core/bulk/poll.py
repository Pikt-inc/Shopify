from typing import Optional, Iterator
import requests
from requests.exceptions import RequestException
import json
import time

from shopify_sdk import client as default_client
from shopify_sdk.gql.core.client import ShopifyClient
from shopify_sdk.gql.core.types import ID
from shopify_sdk.gql.core.types.payload import BulkOperationResultPayload
from shopify_sdk.gql.queries import bulkOperation
from shopify_sdk.gql.core.types.objects import BulkOperation

DOWNLOAD_TIMEOUT_S = 300  # 5 minutes
UPLOAD_TIMEOUT_S = 600  # 10 minutes
POLL_INTERVAL_S = 5  # 5 seconds

class BulkActionResultManager:
    """
    Manages polling of bulk actions until completion.
    Yields responses
    """

    def __init__(
        self,
        bulk_operation_id: ID,
        client: Optional["ShopifyClient"] = default_client,
    ):
        self._client = client
        self._bulk_operation_id = bulk_operation_id

    @classmethod
    def yield_results(
        cls,
        bulk_operation_id: ID,
        client: Optional["ShopifyClient"] = default_client,
    ) -> Iterator[BulkOperationResultPayload]:
        runner = cls(
            bulk_operation_id=bulk_operation_id,
            client=client,
        )
        operation = runner._poll_operation()
        if operation.status != "COMPLETED":
            raise ValueError(
                f"Bulk operation did not complete successfully. "
                f"Status: {operation.status}, "
                f"Error Code: {operation.error_code}, "
                f"Message: {operation.error_message}"
            )
        if not operation.url:
            return None

        yield from runner._iter_bulk_operation_results(
            results_url=operation.url,
            timeout_s=DOWNLOAD_TIMEOUT_S,
        )

    def _poll_operation(
        self
    ) -> BulkOperation:
        terminal_statuses = {"COMPLETED", "FAILED", "CANCELED", "CANCELLED", "EXPIRED"}
        deadline = time.monotonic() + UPLOAD_TIMEOUT_S
        remaining = deadline - time.monotonic()
        while remaining > 0:
            operation = self._get_operation_status()
            if operation.status in terminal_statuses:
                return operation
            remaining = deadline - time.monotonic()
        time.sleep(min(POLL_INTERVAL_S, remaining))

    def _get_operation_status(
        self
    ) -> BulkOperation:
        operation = bulkOperation(id=self._bulk_operation_id).execute(client=self._client)
        if operation is None:
            raise ValueError(f"No bulk operation found for id={self._bulk_operation_id!r}.")
        return operation
    
    def _iter_bulk_operation_results(
        self,
        results_url: str,
        *,
        timeout_s: float = DOWNLOAD_TIMEOUT_S,
    ) -> Iterator[BulkOperationResultPayload]:
        display_url = results_url
        response = None
        try:
            response = requests.get(results_url, stream=True, timeout=timeout_s)
            response.raise_for_status()

            for line_number, line in enumerate(response.iter_lines(decode_unicode=True), start=1):
                if not line:
                    continue
                try:
                    if json.loads(line).get('__lineNumber'):  # Mutation
                        yield BulkOperationResultPayload.model_validate_json(
                            line.strip()
                        )
                    else:  # Query
                        yield line
                except json.JSONDecodeError as e:
                    snippet = line[:500]
                    raise ValueError(
                        f"Invalid JSON in bulk results from {display_url} at line {line_number}: {snippet}"
                    ) from e
        except RequestException as e:
            raise ValueError(f"Failed to download bulk results from {display_url}: {e}") from e
        finally:
            if response is not None:
                response.close()


