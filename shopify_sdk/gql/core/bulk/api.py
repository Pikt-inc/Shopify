"""Public compatibility façade for submitting Shopify bulk operations."""

from collections.abc import Iterator
from typing import TYPE_CHECKING

from shopify_sdk.gql.core.query import Query

if TYPE_CHECKING:
    from shopify_sdk.gql.core.mutation import Mutation
    from shopify_sdk.gql.core.types.payload import BulkOperationResultPayload

    from .poll import BulkOperationHandle


def bulk_mutation(
    mutations: list["Mutation"],
) -> Iterator["BulkOperationResultPayload"]:
    """Submit bulk mutations and yield their legacy parsed result payloads."""
    from .mutation import BulkMutationRunner

    runner = BulkMutationRunner(mutations=mutations)
    yield from runner.run()


def bulk_query(query: Query) -> Iterator["BulkOperationResultPayload"]:
    """Submit a bulk query and yield its legacy parsed result payloads."""
    from .query import BulkQueryRunner

    if not isinstance(query, Query):
        raise TypeError("query must be a Query instance.")
    yield from BulkQueryRunner(query=query).run()


def bulk_query_handle(query: Query) -> "BulkOperationHandle":
    """Submit a bulk query and return a checkpoint-capable operation handle."""
    from .query import BulkQueryRunner

    if not isinstance(query, Query):
        raise TypeError("query must be a Query instance.")
    return BulkQueryRunner(query=query).handle
