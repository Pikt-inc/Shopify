from typing import Any, Iterator, TYPE_CHECKING

from .query import Query

if TYPE_CHECKING:
    from shopify_sdk.gql.core.types.objects import BulkOperationResultPayload


class Mutation(Query):
    action_type: str = "mutation"

    def __init__(
        self,
    ):
        super().__init__()

    @classmethod
    def bulk(
        cls,
        mutations: list["Mutation"]
    ) -> Iterator["BulkOperationResultPayload"]:
        """
        Execute a bulk mutation operation.
        Args:
            mutations (list[Mutation]): A list of Mutation instances to be executed in bulk.
        Returns:
            Iterator[BulkOperationResult]: An iterator over the results of the bulk operation.
        """
        from .bulk import bulk_mutation
        responses = bulk_mutation(
            mutations=mutations,
        )
        for response in responses:
            yield response

    def _serialize_value(self, value: Any) -> Any:
        if hasattr(value, "to_graphql"):
            return value.to_graphql()
        if isinstance(value, list):
            return [self._serialize_value(item) for item in value]
        if isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        return value