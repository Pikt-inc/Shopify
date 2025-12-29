from typing import Any, Iterator, TYPE_CHECKING, List

from pydantic import BaseModel

from .query import Query

if TYPE_CHECKING:
    from shopify_sdk.gql.core.types.payload import BulkOperationResultPayload


class Mutation(Query):
    action_type: str = "mutation"

    def __init__(
        self,
    ):
        super().__init__()

    @classmethod
    def bulk(  # type: ignore[override]
        cls,
        mutations: List["Mutation"]
    ) -> Iterator[BaseModel]:
        """
        Execute a bulk mutation operation.
        Args:
            mutations (list[Mutation]): A list of Mutation instances to be executed in bulk.
        Returns:
            Iterator[BaseModel]: An iterator over the payload models returned by the bulk operation.
        """
        from .bulk import bulk_mutation
        responses: Iterator["BulkOperationResultPayload"] = bulk_mutation(
            mutations=mutations,
        )
        return_type = mutations[0].return_type
        if return_type is None:
            raise ValueError("return_type must be defined for bulk mutations.")
        for response in responses:
            response_data = response.data
            if response_data is None:
                raise ValueError("Bulk mutation result payload is missing data.")
            if not isinstance(response_data, dict):
                raise TypeError(
                    f"Bulk mutation result payload must be a dictionary, got {type(response_data).__name__}."
                )
            mutation_data = response_data.get(cls.__name__)
            if mutation_data is None:
                raise ValueError(f"Bulk mutation result payload missing key '{cls.__name__}'.")
            if not isinstance(mutation_data, dict):
                raise TypeError(
                    f"Bulk mutation result payload for '{cls.__name__}' must be a dictionary, got {type(mutation_data).__name__}."
                )
            yield mutations[0]._build_partial_model(
                mutation_data,
                return_type
            )
