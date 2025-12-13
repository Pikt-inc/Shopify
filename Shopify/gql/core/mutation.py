from typing import Any, Dict

from .query import Query
from .client import ShopifyClient
from .exceptions import MutationExecutionError


class Mutation(Query):

    def __init__(
        self,
    ):
        super().__init__()

    @property
    def _input_arguments(self) -> Dict[str, Any]:
        return {
            name: value
            for name, value in super()._input_arguments.items()
            if value is not None
        }

    @property
    def fields(self) -> str:
        return self._user_errors_block

    @property
    def _user_errors_block(self) -> str:
        spacer = " " * (self._indent * 2)
        inner = " " * (self._indent * 3)
        return "\n".join(
            [
                f"{spacer}userErrors {{",
                f"{inner}field",
                f"{inner}message",
                f"{spacer}}}",
            ]
        )

    @property
    def body(self) -> str:
        args_list = self._input_arguments
        args_string = ", ".join(f"{name}: ${name}" for name in args_list.keys())

        return "\n".join(
            [
                f"mutation {self.class_name}({self.arguments}) {{",
                f"{' ' * self._indent}{self.class_name}({args_string}) {{",
                f"{self.fields}",
                f"{' ' * self._indent}}}",
                "}",
            ]
        )

    def _serialize_value(self, value: Any) -> Any:
        if hasattr(value, "to_graphql"):
            return value.to_graphql()
        if isinstance(value, list):
            return [self._serialize_value(item) for item in value]
        if isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        return value

    def execute(self, client: ShopifyClient) -> Dict[str, Any]:
        variables = {
            name: self._serialize_value(value)
            for name, value in self._input_arguments.items()
        }

        response = client.request(query=self.body, variables=variables)

        payload = response.data.get(self.class_name) if response.data else None
        if payload is None:
            raise ValueError("Response data is None.")
        if not isinstance(payload, dict):
            raise TypeError(f"Expected mutation payload to be a dict, got {type(payload).__name__}.")

        user_errors = payload.get("userErrors", [])
        if user_errors:
            raise MutationExecutionError(user_errors)
        
        return payload
