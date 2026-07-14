from importlib import import_module
from types import ModuleType
from unittest.mock import patch

import pytest

from shopify_sdk.gql.core.bulk import (
    BulkOperationSubmissionError,
    BulkSubmissionStage,
)
from shopify_sdk.gql.core.bulk.mutation import BulkMutationRunner
from shopify_sdk.gql.core.bulk.query import BulkQueryRunner
from shopify_sdk.gql.core.bulk.upload import JSONUploadManager
from shopify_sdk.gql.core.mutation import Mutation
from shopify_sdk.gql.core.query import Query


class StaticBulkQuery(Query):
    """Provide a minimal inline GraphQL query for submission tests."""

    def inline_body(self) -> str:
        """Return a valid minimal bulk query document."""
        return "query { shop { id } }"


class StaticBulkMutation(Mutation):
    """Provide a minimal inline mutation body for bulk submission tests."""

    def __init__(self) -> None:
        """Initialize one required input argument for mutation validation."""
        super().__init__()
        self.identifier = "test"

    @property
    def body(self) -> str:
        """Return a minimal mutation body without requiring model selection fields."""
        return "mutation { productDelete(input: {id: \"gid://shopify/Product/1\"}) { userErrors { message } } }"


class FakeSubmission:
    def __init__(self, payload: object) -> None:
        """Store a payload returned when the fake Shopify mutation executes."""
        self._payload = payload

    def execute(self, client: object) -> object:
        """Return the configured typed Shopify payload."""
        return self._payload


def payload_module(version: str) -> ModuleType:
    """Import the version-specific Shopify payload models under test."""
    return import_module(f"shopify_sdk.gql.versions.{version}.types.payload")


def assert_error(
    captured_error: pytest.ExceptionInfo[BulkOperationSubmissionError],
    stage: BulkSubmissionStage,
    *,
    code: str | None,
    field: tuple[str, ...],
    message: str,
) -> None:
    """Assert stable mapped Shopify user-error details without raw payload access."""
    error = captured_error.value
    assert error.stage is stage
    assert len(error.errors) == 1
    assert error.errors[0].code == code
    assert error.errors[0].field == field
    assert error.errors[0].message == message
    assert "payload" not in error.__dict__


@pytest.mark.parametrize("version", ["v2025_10", "v2026_07"])
def test_bulk_query_submission_raises_typed_user_error(version: str) -> None:
    """Map versioned bulk-query user errors into the stable public exception."""
    payloads = payload_module(version)
    payload = payloads.BulkOperationRunQueryPayload.model_validate(
        {
            "bulkOperation": None,
            "userErrors": [
                {
                    "code": "INVALID",
                    "field": ["query"],
                    "message": "Invalid bulk query.",
                }
            ],
        }
    )
    runner = BulkQueryRunner(query=StaticBulkQuery())

    with patch(
        "shopify_sdk.gql.core.bulk.query.bulkOperationRunQuery",
        return_value=FakeSubmission(payload),
    ):
        with pytest.raises(BulkOperationSubmissionError) as captured_error:
            _ = runner.operation_id

    assert_error(
        captured_error,
        BulkSubmissionStage.BULK_QUERY,
        code="INVALID",
        field=("query",),
        message="Invalid bulk query.",
    )


@pytest.mark.parametrize("version", ["v2025_10", "v2026_07"])
def test_bulk_mutation_submission_raises_typed_user_error(version: str) -> None:
    """Map versioned bulk-mutation user errors into the stable public exception."""
    payloads = payload_module(version)
    payload = payloads.BulkOperationRunMutationPayload.model_validate(
        {
            "bulkOperation": None,
            "userErrors": [
                {
                    "code": "INVALID_MUTATION",
                    "field": ["mutation"],
                    "message": "Invalid bulk mutation.",
                }
            ],
        }
    )
    runner = BulkMutationRunner(mutations=[StaticBulkMutation()])

    with patch(
        "shopify_sdk.gql.mutations.bulkOperationRunMutation",
        return_value=FakeSubmission(payload),
    ):
        with pytest.raises(BulkOperationSubmissionError) as captured_error:
            runner._start_mutation(staged_upload_path="tmp/bulk.jsonl")

    assert_error(
        captured_error,
        BulkSubmissionStage.BULK_MUTATION,
        code="INVALID_MUTATION",
        field=("mutation",),
        message="Invalid bulk mutation.",
    )


@pytest.mark.parametrize("version", ["v2025_10", "v2026_07"])
def test_staged_upload_submission_raises_typed_user_error(version: str) -> None:
    """Map staged-upload errors without fabricating a bulk-operation error code."""
    payloads = payload_module(version)
    payload = payloads.StagedUploadsCreatePayload.model_validate(
        {
            "stagedTargets": [],
            "userErrors": [
                {
                    "field": ["input", "0", "filename"],
                    "message": "Filename is invalid.",
                }
            ],
        }
    )
    manager = JSONUploadManager(content=b"{}\n", filename="bulk.jsonl")

    with patch(
        "shopify_sdk.gql.core.bulk.upload.stagedUploadsCreate",
        return_value=FakeSubmission(payload),
    ):
        with pytest.raises(BulkOperationSubmissionError) as captured_error:
            _ = manager.stage

    assert_error(
        captured_error,
        BulkSubmissionStage.STAGED_UPLOAD,
        code=None,
        field=("input", "0", "filename"),
        message="Filename is invalid.",
    )
