from types import SimpleNamespace
from unittest.mock import patch
from datetime import datetime

import pytest

from shopify_sdk.gql.core.bulk import (
    BulkFlatOperationResult,
    BulkOperationCheckpoint,
    BulkOperationHandle,
    BulkOperationTerminalError,
    bulk_query_handle,
)
from shopify_sdk.gql.core.bulk.poll import BulkActionResultManager
from shopify_sdk.gql.core.bulk.query import BulkQueryRunner
from shopify_sdk.gql.core.query import Query
from shopify_sdk.gql.versions.v2025_10.types.payload import (
    BulkOperationResultPayload as BulkOperationResultPayload2025,
)


class FakeResponse:
    def __init__(self, lines: list[str]) -> None:
        """Store JSONL lines returned by the fake streamed response."""
        self._lines = lines
        self.closed = False

    def raise_for_status(self) -> None:
        """Simulate a successful result-file response."""

    def iter_lines(self, decode_unicode: bool) -> list[str]:
        """Return configured JSONL records for the streaming parser."""
        assert decode_unicode is True
        return self._lines

    def close(self) -> None:
        """Record response cleanup."""
        self.closed = True


class StaticBulkQuery(Query):
    def inline_body(self) -> str:
        """Return a minimal query body without requiring a Shopify connection."""
        return "query { shop { id } }"


class FakeBulkQuerySubmission:
    def __init__(self, operation_id: str) -> None:
        """Store the operation identifier returned when the fake mutation executes."""
        self._operation_id = operation_id

    def execute(self, client: object) -> object:
        """Return a minimal bulk operation submission payload."""
        return SimpleNamespace(
            bulkOperation=SimpleNamespace(id=self._operation_id),
            userErrors=[],
        )


def completed_operation(results_url: str = "https://example.test/results.jsonl") -> object:
    """Create a minimal successful terminal operation for polling tests."""
    return SimpleNamespace(
        id="gid://shopify/BulkOperation/1",
        status="COMPLETED",
        errorCode=None,
        url=results_url,
        partialDataUrl=None,
        objectCount=2,
        fileSize=24,
        createdAt=datetime(2026, 1, 1),
        completedAt=None,
    )


class TestBulkOperationTerminalState:
    def test_bulk_query_handle_returns_submitted_query_handle(self) -> None:
        """Expose an operation handle immediately after submitting a bulk query."""
        expected_handle = object()
        fake_runner = SimpleNamespace(handle=expected_handle)
        query = Query()

        with patch(
            "shopify_sdk.gql.core.bulk.query.BulkQueryRunner",
            return_value=fake_runner,
        ) as runner_class:
            handle = bulk_query_handle(query, group_objects=False)

        assert handle is expected_handle
        runner_class.assert_called_once_with(query=query, group_objects=False)

    @pytest.mark.parametrize(
        ("group_objects", "expected_group_objects"),
        [(True, True), (False, False)],
    )
    def test_query_runner_passes_explicit_grouping_option(
        self,
        group_objects: bool,
        expected_group_objects: bool,
    ) -> None:
        """Send the requested Shopify grouping option when submitting a bulk query."""
        submitted_arguments: list[dict[str, object]] = []

        def submit_bulk_query(**kwargs: object) -> FakeBulkQuerySubmission:
            """Capture GraphQL mutation arguments and return a successful submission."""
            submitted_arguments.append(kwargs)
            return FakeBulkQuerySubmission("gid://shopify/BulkOperation/1")

        runner = BulkQueryRunner(
            query=StaticBulkQuery(),
            group_objects=group_objects,
        )
        with patch(
            "shopify_sdk.gql.core.bulk.query.bulkOperationRunQuery",
            side_effect=submit_bulk_query,
        ):
            assert runner.operation_id == "gid://shopify/BulkOperation/1"

        assert submitted_arguments == [
            {
                "query": "query { shop { id } }",
                "groupObjects": expected_group_objects,
            }
        ]

    def test_query_runner_rejects_non_boolean_grouping_option(self) -> None:
        """Reject invalid grouping flags before making a Shopify mutation request."""
        with pytest.raises(TypeError, match="must be a boolean"):
            BulkQueryRunner(
                query=StaticBulkQuery(),
                group_objects="false",  # type: ignore[arg-type]
            )

    def test_terminal_failure_preserves_shopify_error_metadata(self) -> None:
        """Expose failed terminal status, error code, and partial-result URL."""
        failed_operation = SimpleNamespace(
            id="gid://shopify/BulkOperation/1",
            status="FAILED",
            errorCode="INTERNAL_SERVER_ERROR",
            url=None,
            partialDataUrl="https://example.test/partial.jsonl",
            objectCount=3,
            fileSize=42,
            createdAt=datetime(2026, 1, 1),
            completedAt=None,
        )
        manager = BulkActionResultManager("gid://shopify/BulkOperation/1")

        with patch.object(manager, "_poll_operation", return_value=failed_operation):
            with pytest.raises(BulkOperationTerminalError) as captured_error:
                list(manager.iter_result_events())

        state = captured_error.value.state
        assert state.status == "FAILED"
        assert state.error_code == "INTERNAL_SERVER_ERROR"
        assert state.partial_data_url == "https://example.test/partial.jsonl"
        assert "errorCode: INTERNAL_SERVER_ERROR" in str(captured_error.value)

    def test_handle_returns_typed_terminal_state(self) -> None:
        """Allow callers to inspect terminal metadata without starting a download."""
        handle = BulkOperationHandle("gid://shopify/BulkOperation/1")

        with patch.object(
            handle._manager,
            "_poll_operation",
            return_value=completed_operation(),
        ):
            state = handle.wait_for_terminal_state()

        assert state.is_successful is True
        assert state.object_count == 2
        assert state.file_size == 24
        assert state.created_at == datetime(2026, 1, 1)


class TestBulkResultParsing:
    def test_result_events_preserve_metadata_and_successor_checkpoint(self) -> None:
        """Preserve Shopify provenance and expose the checkpoint after each result."""
        response = FakeResponse(
            [
                '{"productCreate":{"product":{"id":"one"}},"__lineNumber":8,"__parentId":"parent"}',
                '{"productCreate":{"product":{"id":"two"}}}',
            ]
        )
        manager = BulkActionResultManager("gid://shopify/BulkOperation/1")

        with (
            patch.object(manager, "_poll_operation", return_value=completed_operation()),
            patch(
                "shopify_sdk.gql.core.bulk.poll.requests.get",
                return_value=response,
            ),
        ):
            results = list(manager.iter_result_events())

        assert results[0].payload.lineNumber == 8
        assert results[0].payload.parentId == "parent"
        assert results[0].payload.data == {
            "productCreate": {"product": {"id": "one"}},
            "__lineNumber": 8,
            "__parentId": "parent",
        }
        assert results[0].checkpoint == BulkOperationCheckpoint(
            operation_id="gid://shopify/BulkOperation/1",
            next_line_number=2,
        )
        assert results[1].payload.lineNumber == 2
        assert results[1].checkpoint.next_line_number == 3
        assert response.closed is True

    def test_resume_skips_acknowledged_physical_lines(self) -> None:
        """Reattach to a completed operation without re-emitting acknowledged results."""
        response = FakeResponse(
            [
                '{"id":"first"}',
                "",
                '{"id":"second","__parentId":"parent"}',
            ]
        )
        checkpoint = BulkOperationCheckpoint(
            operation_id="gid://shopify/BulkOperation/1",
            next_line_number=3,
        )
        manager = BulkActionResultManager("gid://shopify/BulkOperation/1")

        with (
            patch.object(manager, "_poll_operation", return_value=completed_operation()),
            patch(
                "shopify_sdk.gql.core.bulk.poll.requests.get",
                return_value=response,
            ),
        ):
            results = list(manager.iter_result_events(checkpoint=checkpoint))

        assert results[0].payload.data == {
            "id": "second",
            "__parentId": "parent",
        }
        assert results[0].payload.parentId == "parent"
        assert results[0].checkpoint.next_line_number == 4

    def test_flat_result_events_remove_metadata_and_preserve_parent_links(self) -> None:
        """Map root and child JSONL records into typed flat records."""
        response = FakeResponse(
            [
                '{"id":"root","__lineNumber":10}',
                '{"id":"child","__parentId":"root","errors":[{"code":"INVALID"}]}',
            ]
        )
        manager = BulkActionResultManager("gid://shopify/BulkOperation/1")

        with (
            patch.object(manager, "_poll_operation", return_value=completed_operation()),
            patch(
                "shopify_sdk.gql.core.bulk.poll.requests.get",
                return_value=response,
            ),
        ):
            results = list(manager.iter_flat_result_events())

        assert all(isinstance(result, BulkFlatOperationResult) for result in results)
        assert results[0].record.data == {"id": "root"}
        assert results[0].record.line_number == 10
        assert results[0].record.parent_id is None
        assert results[1].record.data == {"id": "child"}
        assert results[1].record.parent_id == "root"
        assert results[1].record.errors == [{"code": "INVALID"}]
        assert results[1].checkpoint.next_line_number == 3

    def test_flat_result_resume_skips_acknowledged_records(self) -> None:
        """Resume flat record iteration from the checkpoint's physical line number."""
        response = FakeResponse(
            [
                '{"id":"first"}',
                "",
                '{"id":"second","__parentId":"parent"}',
            ]
        )
        checkpoint = BulkOperationCheckpoint(
            operation_id="gid://shopify/BulkOperation/1",
            next_line_number=3,
        )
        manager = BulkActionResultManager("gid://shopify/BulkOperation/1")

        with (
            patch.object(manager, "_poll_operation", return_value=completed_operation()),
            patch(
                "shopify_sdk.gql.core.bulk.poll.requests.get",
                return_value=response,
            ),
        ):
            results = list(manager.iter_flat_result_events(checkpoint=checkpoint))

        assert results[0].record.data == {"id": "second"}
        assert results[0].record.parent_id == "parent"
        assert results[0].checkpoint.next_line_number == 4

    def test_rejects_checkpoint_for_a_different_operation(self) -> None:
        """Prevent a checkpoint from being resumed against another operation."""
        manager = BulkActionResultManager("gid://shopify/BulkOperation/1")
        checkpoint = BulkOperationCheckpoint(
            operation_id="gid://shopify/BulkOperation/2",
        )

        with pytest.raises(ValueError, match="does not match"):
            list(manager.iter_result_events(checkpoint=checkpoint))

    def test_2025_result_payload_preserves_parent_identifier(self) -> None:
        """Keep typed parent provenance available under the older API version."""
        payload = BulkOperationResultPayload2025.model_validate(
            {
                "data": {"id": "child"},
                "__lineNumber": 2,
                "__parentId": "parent",
            }
        )

        assert payload.lineNumber == 2
        assert payload.parentId == "parent"
