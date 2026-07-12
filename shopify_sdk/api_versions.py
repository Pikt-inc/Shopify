from __future__ import annotations

import os
from typing import Mapping, Optional


SHOPIFY_API_VERSION_ENV_VAR = "SHOPIFY_API_VERSION"
DEFAULT_API_VERSION = "2026-07"
SUPPORTED_API_VERSIONS = ("2025-10", "2026-07")

_VERSION_MODULE_NAMES = {
    "2025-10": "v2025_10",
    "2026-07": "v2026_07",
}


class UnsupportedShopifyApiVersion(ValueError):
    """Raised when the SDK lacks a GraphQL implementation for an API version."""


def resolve_api_version(
    explicit_version: Optional[str] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> str:
    """Resolve the Shopify API version from explicit input, environment, or default.

    :param explicit_version: API version supplied by the caller.
    :param environ: Optional environment mapping for tests or custom process state.
    :returns: The selected API version string.
    """
    env = os.environ if environ is None else environ
    return explicit_version or env.get(SHOPIFY_API_VERSION_ENV_VAR) or DEFAULT_API_VERSION


def version_module_name(api_version: str) -> str:
    """Return the Python module suffix for a supported Shopify API version.

    :param api_version: Shopify API version such as ``2026-07``.
    :returns: Module suffix such as ``v2026_07``.
    :raises UnsupportedShopifyApiVersion: If no implementation exists.
    """
    try:
        return _VERSION_MODULE_NAMES[api_version]
    except KeyError as exc:
        supported = ", ".join(SUPPORTED_API_VERSIONS)
        raise UnsupportedShopifyApiVersion(
            f"Shopify API version {api_version!r} is not supported by this SDK. "
            f"Supported versions: {supported}."
        ) from exc
