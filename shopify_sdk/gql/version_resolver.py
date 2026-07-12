from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from types import ModuleType

from shopify_sdk.api_versions import version_module_name


@dataclass(frozen=True)
class GraphQLVersionModules:
    """Modules that make up one Shopify Admin GraphQL API implementation."""

    api_version: str
    types: ModuleType
    queries: ModuleType
    mutations: ModuleType
    bulk: ModuleType


class GraphQLVersionResolver:
    """Resolve versioned GraphQL implementation modules by Shopify API version."""

    def __init__(self) -> None:
        """Initialize an empty module cache for resolved API versions."""
        self._cache: dict[str, GraphQLVersionModules] = {}

    def resolve(self, api_version: str) -> GraphQLVersionModules:
        """Return versioned GraphQL modules for a supported API version.

        :param api_version: Shopify API version such as ``2026-07``.
        :returns: Loaded query, mutation, type, and bulk modules.
        """
        if api_version not in self._cache:
            self._cache[api_version] = self._load(api_version)
        return self._cache[api_version]

    def _load(self, api_version: str) -> GraphQLVersionModules:
        """Import the module bundle for a supported API version."""
        module_name = version_module_name(api_version)
        package = f"shopify_sdk.gql.versions.{module_name}"
        return GraphQLVersionModules(
            api_version=api_version,
            types=import_module(f"{package}.types"),
            queries=import_module(f"{package}.queries"),
            mutations=import_module(f"{package}.mutations"),
            bulk=import_module(f"{package}.bulk"),
        )


version_resolver = GraphQLVersionResolver()
