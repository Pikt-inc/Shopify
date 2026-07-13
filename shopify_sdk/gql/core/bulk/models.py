"""Typed terminal state and checkpoint contracts for bulk operations."""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Protocol

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from shopify_sdk.gql.core.types.payload import BulkOperationResultPayload


class SupportsBulkOperation(Protocol):
    """Describe fields required to preserve a terminal bulk operation state."""

    @property
    def id(self) -> str:
        """Return the bulk operation identifier."""

    @property
    def status(self) -> str:
        """Return the Shopify bulk operation status."""

    @property
    def errorCode(self) -> str | None:
        """Return the terminal error code when Shopify supplied one."""

    @property
    def url(self) -> str | None:
        """Return the full-result download URL when available."""

    @property
    def partialDataUrl(self) -> str | None:
        """Return the partial-result download URL when available."""

    @property
    def objectCount(self) -> int | None:
        """Return the processed object count when Shopify supplied one."""

    @property
    def fileSize(self) -> int | None:
        """Return the result-file size when Shopify supplied one."""

    @property
    def completedAt(self) -> datetime | None:
        """Return the terminal completion timestamp when available."""

    @property
    def createdAt(self) -> datetime:
        """Return the operation creation timestamp."""


class BulkOperationCheckpoint(BaseModel):
    """Persistable position for resuming JSONL result processing."""

    operation_id: str
    next_line_number: int = Field(default=1, ge=1)
    model_config = ConfigDict(frozen=True)


class BulkOperationTerminalState(BaseModel):
    """Terminal bulk-operation metadata preserved from Shopify's response."""

    operation_id: str
    status: str
    error_code: str | None = None
    result_url: str | None = None
    partial_data_url: str | None = None
    object_count: int | None = None
    file_size: int | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None
    model_config = ConfigDict(frozen=True)

    @property
    def is_successful(self) -> bool:
        """Return whether Shopify reported the operation as completed."""
        return self.status == "COMPLETED"

    @classmethod
    def from_operation(
        cls,
        operation: SupportsBulkOperation,
    ) -> "BulkOperationTerminalState":
        """Map a Shopify operation model into stable terminal metadata."""
        return cls(
            operation_id=operation.id,
            status=operation.status,
            error_code=operation.errorCode,
            result_url=operation.url,
            partial_data_url=operation.partialDataUrl,
            object_count=operation.objectCount,
            file_size=operation.fileSize,
            created_at=operation.createdAt,
            completed_at=operation.completedAt,
        )


class BulkOperationTerminalError(ValueError):
    """Raised when a bulk operation reaches a non-successful terminal state."""

    def __init__(self, state: BulkOperationTerminalState) -> None:
        """Preserve terminal state while formatting a backward-compatible error message."""
        self.state = state
        super().__init__(self._message(state))

    @staticmethod
    def _message(state: BulkOperationTerminalState) -> str:
        """Format a terminal failure with Shopify's diagnostic metadata."""
        details = [f"status: {state.status}"]
        if state.error_code:
            details.append(f"errorCode: {state.error_code}")
        if state.partial_data_url:
            details.append(f"partialDataUrl: {state.partial_data_url}")
        return "Bulk operation did not complete successfully. " + ", ".join(details)


@dataclass(frozen=True)
class BulkOperationResult:
    """A parsed bulk result payload with its next resumable checkpoint."""

    payload: "BulkOperationResultPayload"
    checkpoint: BulkOperationCheckpoint
