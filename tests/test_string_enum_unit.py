"""Tests for Python 3.10-compatible string enumeration behavior."""

from shopify_sdk.gql.core.bulk.models import BulkSubmissionStage
from shopify_sdk.gql.core.client.retry import RequestRetryMode


def test_string_enums_format_as_their_raw_values() -> None:
    """Match ``enum.StrEnum`` string behavior on every supported Python version."""

    assert str(RequestRetryMode.NEVER) == "never"
    assert f"{BulkSubmissionStage.BULK_QUERY}" == "bulk_query"
