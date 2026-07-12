from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, cast

from shopify_sdk.gql.core.client import current_api_version
from shopify_sdk.gql.version_resolver import version_resolver

if TYPE_CHECKING:
    from pydantic import BaseModel

    from shopify_sdk.gql.core.mutation import Mutation


class VersionedGraphQLSymbol:
    """Callable proxy that resolves a query or mutation class by active API version."""

    def __init__(self, module_name: str, symbol_name: str) -> None:
        """Store the versioned module and symbol names to resolve later.

        :param module_name: Version bundle module name, such as ``queries``.
        :param symbol_name: Query or mutation class name to resolve.
        """
        self._module_name = module_name
        self._symbol_name = symbol_name

    @property
    def __name__(self) -> str:
        """Return the proxied GraphQL class name for compatibility."""
        return self._symbol_name

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Instantiate the active version's GraphQL class."""
        return self._symbol()(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Delegate class attributes to the active version's GraphQL class."""
        return getattr(self._symbol(), name)

    def bulk(self, mutations: list[Mutation]) -> Iterator[BaseModel]:
        """Execute bulk mutations using the mutation class that created the items."""
        if mutations:
            yield from mutations[0].__class__.bulk(mutations)
            return
        yield from self._symbol().bulk(mutations)

    def _symbol(self) -> type[Any]:
        """Return the active version's query or mutation class."""
        modules = version_resolver.resolve(current_api_version())
        module = getattr(modules, self._module_name)
        return cast(type[Any], getattr(module, self._symbol_name))

    def __repr__(self) -> str:
        """Return a debug representation of the proxied symbol."""
        return f"<VersionedGraphQLSymbol {self._module_name}.{self._symbol_name}>"
