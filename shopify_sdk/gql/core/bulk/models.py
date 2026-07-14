"""Typed terminal state and checkpoint contracts for bulk operations."""

from dataclasses import dataclass
from datetime import datetime
from collections.abc import Sequence
from enum import StrEnum
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


class BulkSubmissionStage(StrEnum):
    """Identify the Shopify bulk workflow step that rejected a submission."""

    BULK_MUTATION = "bulk_mutation"
    BULK_QUERY = "bulk_query"
    STAGED_UPLOAD = "staged_upload"


class SupportsSubmissionUserError(Protocol):
    """Describe common Shopify user-error fields across bulk submission payloads."""

    @property
    def field(self) -> Sequence[str] | None:
        """Return the Shopify input field path when available."""

    @property
    def message(self) -> str:
        """Return Shopify's safe human-readable user error message."""


class SupportsCodedSubmissionUserError(SupportsSubmissionUserError, Protocol):
    """Describe bulk-operation user errors that also expose a machine-readable code."""

    @property
    def code(self) -> str | None:
        """Return Shopify's optional bulk-operation user-error code."""


class BulkSubmissionUserError(BaseModel):
    """Stable typed representation of one Shopify bulk submission user error."""

    code: str | None = None
    field: tuple[str, ...] | None = None
    message: str
    model_config = ConfigDict(frozen=True)


class BulkOperationSubmissionError(ValueError):
    """Raised when Shopify rejects a bulk query, mutation, or staged upload submission."""

    def __init__(
        self,
        stage: BulkSubmissionStage,
        errors: Sequence[BulkSubmissionUserError],
    ) -> None:
        """Preserve typed Shopify user errors without retaining an entire response payload."""
        self.stage = stage
        self.errors = tuple(errors)
        super().__init__(self._message(stage, self.errors))

    @staticmethod
    def _message(
        stage: BulkSubmissionStage,
        errors: Sequence[BulkSubmissionUserError],
    ) -> str:
        """Format a safe submission failure summary from Shopify user-error messages."""
        messages = "; ".join(error.message for error in errors)
        return f"Shopify {stage.value} submission failed: {messages}"


class BulkSubmissionErrorMapper:
    """Map versioned Shopify user-error models into stable bulk submission errors."""

    @classmethod
    def from_bulk_operation_errors(
        cls,
        stage: BulkSubmissionStage,
        errors: Sequence[SupportsCodedSubmissionUserError],
    ) -> BulkOperationSubmissionError:
        """Map coded bulk-operation user errors from query or mutation submission."""
        return BulkOperationSubmissionError(
            stage=stage,
            errors=[
                BulkSubmissionUserError(
                    code=error.code,
                    field=cls._field_path(error.field),
                    message=error.message,
                )
                for error in errors
            ],
        )

    @classmethod
    def from_staged_upload_errors(
        cls,
        errors: Sequence[SupportsSubmissionUserError],
    ) -> BulkOperationSubmissionError:
        """Map staged-upload user errors, which do not provide Shopify error codes."""
        return BulkOperationSubmissionError(
            stage=BulkSubmissionStage.STAGED_UPLOAD,
            errors=[
                BulkSubmissionUserError(
                    field=cls._field_path(error.field),
                    message=error.message,
                )
                for error in errors
            ],
        )

    @staticmethod
    def _field_path(field: Sequence[str] | None) -> tuple[str, ...] | None:
        """Freeze Shopify's mutable error field path when it is supplied."""
        return tuple(field) if field is not None else None


class BulkFlatRecord(BaseModel):
    """A flat Shopify JSONL record with typed provenance fields."""

    data: dict[str, object]
    line_number: int
    parent_id: str | None = None
    errors: list[dict[str, object]] | None = None
    model_config = ConfigDict(frozen=True)

    @classmethod
    def from_payload(
        cls,
        payload: "BulkOperationResultPayload",
    ) -> "BulkFlatRecord":
        """Map a parsed payload while removing Shopify metadata from business data."""
        if payload.data is None:
            raise ValueError("Bulk flat record payload is missing data.")
        if not isinstance(payload.data, dict):
            raise TypeError(
                "Bulk flat record payload data must be a dictionary, "
                f"got {type(payload.data).__name__}."
            )
        if payload.lineNumber is None:
            raise ValueError("Bulk flat record payload is missing a line number.")
        return cls(
            data=cls._business_data(payload.data),
            line_number=payload.lineNumber,
            parent_id=payload.parentId,
            errors=cls._errors(payload.errors),
        )

    @staticmethod
    def _business_data(data: dict[object, object]) -> dict[str, object]:
        """Remove Shopify JSONL metadata while retaining all business result fields."""
        metadata_keys = {"__lineNumber", "__parentId", "errors"}
        return {
            key: value
            for key, value in data.items()
            if isinstance(key, str) and key not in metadata_keys
        }

    @staticmethod
    def _errors(errors: object) -> list[dict[str, object]] | None:
        """Return typed raw error dictionaries from Shopify's dynamic error payload."""
        if errors is None:
            return None
        if not isinstance(errors, list):
            raise TypeError("Bulk flat record errors must be a list when provided.")
        typed_errors: list[dict[str, object]] = []
        for error in errors:
            if not isinstance(error, dict):
                raise TypeError("Bulk flat record errors must contain dictionaries.")
            typed_errors.append(
                {
                    key: value
                    for key, value in error.items()
                    if isinstance(key, str)
                }
            )
        return typed_errors


@dataclass(frozen=True)
class BulkOperationResult:
    """A parsed bulk result payload with its next resumable checkpoint."""

    payload: "BulkOperationResultPayload"
    checkpoint: BulkOperationCheckpoint

    def as_flat_result(self) -> "BulkFlatOperationResult":
        """Build a flat record event while preserving the successor checkpoint."""
        return BulkFlatOperationResult(
            record=BulkFlatRecord.from_payload(self.payload),
            checkpoint=self.checkpoint,
        )


@dataclass(frozen=True)
class BulkFlatOperationResult:
    """A flat bulk record with its next resumable checkpoint."""

    record: BulkFlatRecord
    checkpoint: BulkOperationCheckpoint
