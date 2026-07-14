"""Public bulk-operation APIs and typed recovery contracts."""

from .api import bulk_mutation, bulk_query, bulk_query_handle
from .models import (
    BulkFlatOperationResult,
    BulkFlatRecord,
    BulkOperationCheckpoint,
    BulkOperationSubmissionError,
    BulkOperationResult,
    BulkOperationTerminalError,
    BulkOperationTerminalState,
    BulkSubmissionStage,
    BulkSubmissionUserError,
)
from .poll import BulkOperationHandle

__all__ = [
    "bulk_mutation",
    "bulk_query",
    "bulk_query_handle",
    "BulkFlatOperationResult",
    "BulkFlatRecord",
    "BulkOperationCheckpoint",
    "BulkOperationSubmissionError",
    "BulkOperationHandle",
    "BulkOperationResult",
    "BulkOperationTerminalError",
    "BulkOperationTerminalState",
    "BulkSubmissionStage",
    "BulkSubmissionUserError",
]
