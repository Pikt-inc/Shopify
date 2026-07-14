"""Polling, terminal-state handling, and resumable JSONL parsing for bulk operations."""

import json
import time
from collections.abc import Iterator
from typing import cast

from pydantic import ValidationError

from shopify_sdk import client as default_client
from shopify_sdk.gql.core.client import ShopifyClient
from shopify_sdk.gql.core.types import ID
from shopify_sdk.gql.core.types.objects import BulkOperation
from shopify_sdk.gql.core.types.payload import BulkOperationResultPayload
from shopify_sdk.gql.queries import bulkOperation

from .models import (
    BulkFlatOperationResult,
    BulkOperationCheckpoint,
    BulkOperationResult,
    BulkOperationTerminalError,
    BulkOperationTerminalState,
    BulkResultParseError,
)
from .download import BulkResultDownloader
from .download import BulkResultLineDownloader

# Starting defaults retained from the prior bulk runner.
# Calibrate these values from operation-duration telemetry.
DOWNLOAD_TIMEOUT_S = 1200
POLL_TIMEOUT_S = 1200
POLL_INTERVAL_S = 5


class BulkActionResultManager:
    """Poll one Shopify bulk operation and expose checkpointed result parsing."""

    def __init__(
        self,
        bulk_operation_id: ID,
        client: ShopifyClient = default_client,
        downloader: BulkResultLineDownloader | None = None,
    ) -> None:
        """Bind the manager to one bulk operation, GraphQL client, and result downloader."""
        self._client = client
        self._bulk_operation_id = bulk_operation_id
        self._downloader = downloader or BulkResultDownloader()

    @classmethod
    def yield_results(
        cls,
        bulk_operation_id: ID,
        client: ShopifyClient = default_client,
        downloader: BulkResultLineDownloader | None = None,
    ) -> Iterator[BulkOperationResultPayload]:
        """Yield legacy result payloads after the operation completes successfully."""
        manager = cls(
            bulk_operation_id=bulk_operation_id,
            client=client,
            downloader=downloader,
        )
        for result in manager.iter_result_events():
            yield result.payload

    def terminal_state(self) -> BulkOperationTerminalState:
        """Wait for a terminal Shopify response and preserve its diagnostic metadata."""
        return BulkOperationTerminalState.from_operation(self._poll_operation())

    def iter_result_events(
        self,
        checkpoint: BulkOperationCheckpoint | None = None,
    ) -> Iterator[BulkOperationResult]:
        """Yield parsed results with the next checkpoint after each emitted JSONL line."""
        active_checkpoint = self._resolve_checkpoint(checkpoint)
        terminal_state = self.terminal_state()
        if not terminal_state.is_successful:
            raise BulkOperationTerminalError(terminal_state)
        if not terminal_state.result_url:
            return
        yield from self._iter_result_events(
            results_url=terminal_state.result_url,
            checkpoint=active_checkpoint,
        )

    def iter_flat_result_events(
        self,
        checkpoint: BulkOperationCheckpoint | None = None,
    ) -> Iterator[BulkFlatOperationResult]:
        """Yield flat records that preserve parent provenance and checkpoints."""
        for result in self.iter_result_events(checkpoint=checkpoint):
            yield result.as_flat_result()

    def _resolve_checkpoint(
        self,
        checkpoint: BulkOperationCheckpoint | None,
    ) -> BulkOperationCheckpoint:
        """Create or validate a checkpoint for this operation."""
        if checkpoint is None:
            return BulkOperationCheckpoint(operation_id=self._bulk_operation_id)
        if checkpoint.operation_id != self._bulk_operation_id:
            raise ValueError("Checkpoint operation_id does not match this bulk operation.")
        return checkpoint

    def _poll_operation(self) -> BulkOperation:
        """Poll until Shopify reports a terminal status or the timeout expires."""
        terminal_statuses = {"COMPLETED", "FAILED", "CANCELED", "CANCELLED", "EXPIRED"}
        deadline = time.monotonic() + POLL_TIMEOUT_S
        while True:
            operation = self._get_operation_status()
            if operation.status in terminal_statuses:
                return operation
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"Bulk operation {self._bulk_operation_id!r} did not complete within "
                    f"{POLL_TIMEOUT_S}s (last status: {operation.status})."
                )
            time.sleep(min(POLL_INTERVAL_S, remaining))

    def _get_operation_status(self) -> BulkOperation:
        """Retrieve the latest state for the configured Shopify bulk operation."""
        operation = cast(
            BulkOperation | None,
            bulkOperation(id=self._bulk_operation_id).execute(client=self._client),
        )
        if operation is None:
            raise ValueError(
                f"No bulk operation found for id={self._bulk_operation_id!r}."
            )
        return operation

    def _iter_result_events(
        self,
        results_url: str,
        checkpoint: BulkOperationCheckpoint,
    ) -> Iterator[BulkOperationResult]:
        """Attach a checkpoint to every unacknowledged parsed result line."""
        for physical_line_number, payload in self._iter_result_lines(
            results_url=results_url,
            start_line_number=checkpoint.next_line_number,
        ):
            yield BulkOperationResult(
                payload=payload,
                checkpoint=BulkOperationCheckpoint(
                    operation_id=self._bulk_operation_id,
                    next_line_number=physical_line_number + 1,
                ),
            )

    def _iter_bulk_operation_results(
        self,
        results_url: str,
        *,
        timeout_s: float = DOWNLOAD_TIMEOUT_S,
        start_line_number: int = 1,
    ) -> Iterator[BulkOperationResultPayload]:
        """Yield legacy payloads, optionally skipping acknowledged physical JSONL lines."""
        for _, payload in self._iter_result_lines(
            results_url=results_url,
            timeout_s=timeout_s,
            start_line_number=start_line_number,
        ):
            yield payload

    def _iter_result_lines(
        self,
        results_url: str,
        *,
        timeout_s: float = DOWNLOAD_TIMEOUT_S,
        start_line_number: int = 1,
    ) -> Iterator[tuple[int, BulkOperationResultPayload]]:
        """Stream and parse unacknowledged JSONL lines with physical line positions."""
        if start_line_number < 1:
            raise ValueError("start_line_number must be at least one.")
        for line_number, line in self._downloader.iter_lines(
            results_url=results_url,
            operation_id=self._bulk_operation_id,
            timeout_s=timeout_s,
            start_line_number=start_line_number,
        ):
            yield line_number, self._parse_result_line(
                line=line,
                line_number=line_number,
                operation_id=self._bulk_operation_id,
            )

    @staticmethod
    def _parse_result_line(
        line: str,
        line_number: int,
        operation_id: str,
    ) -> BulkOperationResultPayload:
        """Normalize Shopify JSONL metadata while retaining the full result record."""
        try:
            parsed_line = json.loads(line)
        except json.JSONDecodeError:
            raise BulkResultParseError(
                operation_id=operation_id,
                line_number=line_number,
                reason="invalid_json",
            ) from None
        if not isinstance(parsed_line, dict):
            raise BulkResultParseError(
                operation_id=operation_id,
                line_number=line_number,
                reason="expected_json_object",
            )
        try:
            return BulkOperationResultPayload.model_validate(
                {
                    "data": parsed_line.get("data", parsed_line),
                    "__lineNumber": parsed_line.get("__lineNumber", line_number),
                    "__parentId": parsed_line.get("__parentId"),
                    "errors": parsed_line.get("errors"),
                }
            )
        except ValidationError:
            raise BulkResultParseError(
                operation_id=operation_id,
                line_number=line_number,
                reason="invalid_payload",
            ) from None


class BulkOperationHandle:
    """Additive API for inspecting and resuming a submitted bulk operation."""

    def __init__(
        self,
        operation_id: ID,
        client: ShopifyClient = default_client,
        downloader: BulkResultLineDownloader | None = None,
    ) -> None:
        """Create a handle for a known Shopify bulk operation identifier."""
        self._manager = BulkActionResultManager(
            bulk_operation_id=operation_id,
            client=client,
            downloader=downloader,
        )

    def wait_for_terminal_state(self) -> BulkOperationTerminalState:
        """Wait for and return the operation's typed terminal Shopify metadata."""
        return self._manager.terminal_state()

    def iter_results(
        self,
        checkpoint: BulkOperationCheckpoint | None = None,
    ) -> Iterator[BulkOperationResult]:
        """Yield unacknowledged parsed results with a successor checkpoint per result."""
        yield from self._manager.iter_result_events(checkpoint=checkpoint)

    def iter_flat_results(
        self,
        checkpoint: BulkOperationCheckpoint | None = None,
    ) -> Iterator[BulkFlatOperationResult]:
        """Yield unacknowledged flat records with a successor checkpoint per result."""
        yield from self._manager.iter_flat_result_events(checkpoint=checkpoint)
