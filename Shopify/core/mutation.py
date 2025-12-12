from typing import Protocol, Dict, Callable
from .client import ShopifyClientWrapper
from .types import ShopifyResource

class ShopifyMutationManager:
    _MUTATIONS: Dict[str, Callable[[], str]] = {}  # Store mutation functions
    _RESOURCE_TYPE: ShopifyResource

    class MutationType:
        CREATE = "create"
        RETRIEVE = "retrieve"
        UPDATE = "update"
        DELETE = "delete"
        ARCHIVE = "archive"

    def __init__(self, client: ShopifyClientWrapper, **kwargs):
        self.client = client

    @classmethod
    def register_mutation(cls, mutation_type: str) -> Callable:
        def decorator(func: Callable[[], str]) -> Callable[[], str]:
            cls._MUTATIONS[mutation_type] = func
            return func

        return decorator
    
    def execute_mutation(self, mutation_type: str, variables: dict) -> dict:
        mutation = self._get_mutation(mutation_type)
        response = self.client.request(query=mutation, variables=variables)
        return response

    def _get_mutation(cls, mutation_type: str) -> str:
        mutation_func = cls._MUTATIONS.get(mutation_type)
        if not mutation_func:
            raise ValueError(f"Mutation type '{mutation_type}' is not registered.")
        return mutation_func()