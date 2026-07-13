from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

import requests
from requests import Response
from requests import Session


class ShopifyHttpResponse(Protocol):
    """Minimal HTTP response contract consumed by the Shopify client."""

    status_code: int
    headers: Mapping[str, str]
    text: str

    def json(self) -> Mapping[str, object]:
        """Return the decoded response JSON mapping."""


class ShopifyTransport(Protocol):
    """HTTP boundary used by the Shopify Admin GraphQL client."""

    def post(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        json: Mapping[str, object],
        timeout: tuple[float, float],
    ) -> ShopifyHttpResponse:
        """Post a GraphQL request and return an HTTP response."""


class RequestsTransport:
    """Requests-backed default transport for Shopify Admin GraphQL calls."""

    def __init__(self, session: Session | None = None) -> None:
        """Initialize the transport with an optional requests session.

        :param session: Reusable HTTP session, when supplied.
        """
        self._session = session or requests.Session()

    def post(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        json: Mapping[str, object],
        timeout: tuple[float, float],
    ) -> Response:
        """Send a JSON POST request through the configured requests session."""
        return self._session.post(
            url,
            headers=dict(headers),
            json=dict(json),
            timeout=timeout,
        )
