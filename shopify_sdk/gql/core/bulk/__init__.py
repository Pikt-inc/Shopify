from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Iterator
from shopify_sdk.gql.core.query import Query

if TYPE_CHECKING:
    from shopify_sdk.gql.core.mutation import Mutation
    from shopify_sdk.gql.core.types.payload import BulkOperationResultPayload

logger = logging.getLogger(__name__)

def bulk_mutation(
    mutations: list["Mutation"],
) -> Iterator["BulkOperationResultPayload"]:
    
    from .mutation import BulkMutationRunner
    bmr = BulkMutationRunner(
        mutations=mutations
    )
    for line in  bmr.run():
        yield line


def bulk_query(
    query: Query
) -> Iterator["BulkOperationResultPayload"]:
    from .query import BulkQueryRunner
    if not isinstance(query, Query):
        raise TypeError("query must be a Query instance.")
    
    bqr = BulkQueryRunner(
        query=query
    )
    for line in  bqr.run():
        yield line

__all__ = [
    "bulk_mutation",
    "bulk_query",
]
