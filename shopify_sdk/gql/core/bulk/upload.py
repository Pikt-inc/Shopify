from __future__ import annotations

import logging
from typing import Any, Mapping
from functools import cached_property

import requests
from requests.exceptions import RequestException
from urllib.parse import urlparse

from shopify_sdk import client as default_client
from shopify_sdk.gql import stagedUploadsCreate
from shopify_sdk.gql.core.types.payload import StagedUploadsCreatePayload
from shopify_sdk.gql.core.types.objects import StagedMediaUploadTarget
from shopify_sdk.gql.core.types.input_objects import StagedUploadInput


UPLOAD_TIMEOUT_S = 300  # 5 minutes

logger = logging.getLogger(__name__)


class JSONUploadManager:
    """
    Manager for uploading JSONL content via staged uploads.
    """

    def __init__(
        self,
        content: bytes,
        filename: str,
        client=default_client,
        mime_type: str = "text/jsonl",
    ):
        self._content = content
        self._client = client
        self._filename = filename
        self._mime_type = mime_type

    @cached_property
    def stage(self) -> StagedUploadsCreatePayload:
        staged: StagedUploadsCreatePayload = stagedUploadsCreate(
            input=[
                StagedUploadInput(
                    resource="BULK_MUTATION_VARIABLES",
                    filename=self._filename,
                    mimeType=self._mime_type,
                    httpMethod="POST",
                    fileSize=len(self._content),
                )
            ],
            field_inclusions={
                "StagedUploadsCreatePayload": set(["stagedTargets", "userErrors"]),
            },
        ).execute(client=self._client)
        if not staged:
            logger.error(f"stagedUploadsCreate returned no payload: {staged}")
            raise ValueError("stagedUploadsCreate returned no payload.")

        return staged

    @property
    def target(self) -> StagedMediaUploadTarget:
        staged_targets = self.stage.stagedTargets
        if not staged_targets:
            raise ValueError(
                "No staged upload targets available from stagedUploadsCreate response."
            )
        return staged_targets[0]

    @cached_property
    def params(self) -> Mapping[str, Any]:
        params: dict[str, str] = {}
        for param in self.target.parameters:
            name = param.name
            value = param.value
            if isinstance(name, str) and isinstance(value, str):
                params[name] = value
        return params

    def upload(self) -> bool:
        try:
            if not self.target.url:
                logger.error("No upload URL available in staged upload target.")
                raise ValueError("No upload URL available in staged upload target.")

            response = requests.post(
                self.target.url,
                data=self.params,
                files={"file": (self._filename, self._content, self._mime_type)},
                timeout=UPLOAD_TIMEOUT_S,
            )
            response.raise_for_status()
            return True
        except RequestException as e:
            logging.error(f"Upload failed: {e}")
            return False

    @cached_property
    def staged_upload_path(self) -> str:
        key: str | None = self.params.get("key")
        if key:
            return key
        resource_url = getattr(self.target, "resourceUrl", None)
        if isinstance(resource_url, str) and resource_url:
            return _derive_staged_upload_path(resource_url)
        # fallback to upload url if nothing else is available
        return self.target.url or ""


def _derive_staged_upload_path(resource_url: str) -> str:
    if resource_url.startswith("http://") or resource_url.startswith("https://"):
        path = urlparse(resource_url).path.lstrip("/")
    else:
        path = resource_url.lstrip("/")

    if path.startswith("bulk/"):
        # strip Shopify's bulk/ bucket prefix
        try:
            path = path.removeprefix("bulk/")
        except AttributeError:
            if path.startswith("bulk/"):
                path = path[len("bulk/") :]
    return path
