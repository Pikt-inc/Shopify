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
    BulkResultDownloadError,
    BulkResultParseError,
    BulkSubmissionStage,
    BulkSubmissionUserError,
)
from .poll import BulkOperationHandle
from .download import BulkDownloadRetryEvent
from .download import BulkResultDownloader
from .download import BulkResultLineDownloader
from .download import BulkResultDownloadRetryPolicy

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
    "BulkResultDownloadError",
    "BulkDownloadRetryEvent",
    "BulkResultDownloader",
    "BulkResultLineDownloader",
    "BulkResultDownloadRetryPolicy",
    "BulkResultParseError",
    "BulkSubmissionStage",
    "BulkSubmissionUserError",
]
