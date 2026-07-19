"""Typed local-image staging for Shopify product mutations."""

from __future__ import annotations

import mimetypes
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Final, Protocol

import requests
from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from shopify_sdk import client
from shopify_sdk.gql import stagedUploadsCreate
from shopify_sdk.gql.core.types.input_objects import StagedUploadInput

SHOPIFY_IMAGE_MAX_BYTES: Final = 20_000_000
_SUPPORTED_IMAGE_TYPES = frozenset({"image/jpeg", "image/png", "image/webp", "image/gif"})


class LocalProductImage(BaseModel):
    """One caller-owned local image staged for a Shopify product mutation."""

    model_config = ConfigDict(frozen=True)

    path: Path
    alt: str | None = Field(default=None, max_length=512)


class StagedProductImage(BaseModel):
    """One uploaded Shopify staging resource ready for immediate mutation use."""

    model_config = ConfigDict(frozen=True)

    original_source: AnyHttpUrl
    filename: str = Field(min_length=1)
    mime_type: str = Field(min_length=1)
    size_bytes: int = Field(gt=0)
    alt: str | None = None


class ProductImageStageResult(BaseModel):
    """Ordered Shopify staging resources corresponding to local inputs."""

    model_config = ConfigDict(frozen=True)

    images: tuple[StagedProductImage, ...]


class ProductImageStageError(ValueError):
    """Safe staged-image failure that never exposes signed upload URLs."""

    def __init__(self, phase: str, message: str, *, image_index: int | None = None) -> None:
        """Initialize one phase-scoped staging error.

        :param phase: Stable failing stage name.
        :param message: Safe failure message without signed URLs.
        :param image_index: Optional zero-based failing image position.
        """

        self.phase = phase
        self.image_index = image_index
        super().__init__(message)


class ProductImageUploadTransportConfig(BaseModel):
    """Starting timeout defaults for one Shopify signed image upload."""

    model_config = ConfigDict(frozen=True)

    connect_timeout_seconds: float = Field(default=10, gt=0)
    read_timeout_seconds: float = Field(default=60, gt=0)


class ImageByteTransport(Protocol):
    """Upload image bytes to one Shopify-provided signed target."""

    def put(self, url: str, payload: bytes, headers: dict[str, str]) -> None:
        """Upload bytes once or raise a transport exception.

        :param url: Ephemeral Shopify-signed upload target.
        :param payload: Exact local image bytes.
        :param headers: Shopify-provided signed request headers.
        """


class RequestsImageByteTransport:
    """Single-attempt requests transport for Shopify signed upload targets."""

    def __init__(self, config: ProductImageUploadTransportConfig | None = None) -> None:
        """Initialize explicit starting connection and upload timeout defaults.

        :param config: Optional typed timeout configuration.
        """

        self._config = config or ProductImageUploadTransportConfig()

    def put(self, url: str, payload: bytes, headers: dict[str, str]) -> None:
        """Upload image bytes without logging signed target details.

        :param url: Ephemeral Shopify-signed upload target.
        :param payload: Exact local image bytes.
        :param headers: Shopify-provided signed request headers.
        :raises ProductImageStageError: If the one upload attempt fails.
        """

        try:
            response = requests.put(
                url,
                data=payload,
                headers=headers,
                timeout=(
                    self._config.connect_timeout_seconds,
                    self._config.read_timeout_seconds,
                ),
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ProductImageStageError("upload", "Shopify staged image upload failed") from exc


StageExecutor = Callable[[list[StagedUploadInput]], object]


class ProductImageStager:
    """Stage immutable local image files without attaching them to a product."""

    def __init__(
        self,
        transport: ImageByteTransport | None = None,
        stage_executor: StageExecutor | None = None,
    ) -> None:
        """Initialize binary transport and typed mutation execution seams.

        :param transport: Optional signed byte-upload transport.
        :param stage_executor: Optional typed staging mutation seam.
        """

        self._transport = transport or RequestsImageByteTransport()
        self._stage_executor = stage_executor or self._execute_stage

    def stage(self, images: Sequence[LocalProductImage]) -> ProductImageStageResult:
        """Upload ordered local files to temporary Shopify staging resources.

        :param images: Ordered caller-owned local images.
        :returns: Ordered immediate-use Shopify resource URLs.
        :raises ProductImageStageError: If validation, staging, or upload fails.
        """

        normalized = tuple(self._normalize(image, index) for index, image in enumerate(images))
        if not normalized:
            return ProductImageStageResult(images=())
        payload = self._stage_executor([item.input for item in normalized])
        targets = self._targets(payload, len(normalized))
        staged = tuple(
            self._upload(item, target, index)
            for index, (item, target) in enumerate(zip(normalized, targets, strict=True))
        )
        return ProductImageStageResult(images=staged)

    @staticmethod
    def _execute_stage(inputs: list[StagedUploadInput]) -> object:
        """Request typed Shopify staging targets without mutation retries."""

        return stagedUploadsCreate(
            input=inputs,
            field_inclusions={
                "StagedUploadsCreatePayload": {"stagedTargets", "userErrors"},
                "StagedMediaUploadTarget": {"parameters", "resourceUrl", "url"},
                "StagedUploadParameter": {"name", "value"},
                "UserError": {"field", "message"},
            },
        ).execute(client=client)

    @staticmethod
    def _targets(payload: object, expected: int) -> tuple[object, ...]:
        """Validate one typed staged-upload mutation result."""

        if payload is None:
            raise ProductImageStageError("stage", "Shopify returned no staged upload payload")
        errors = getattr(payload, "userErrors", None) or []
        if errors:
            messages = "; ".join(str(getattr(error, "message", "unknown error")) for error in errors)
            raise ProductImageStageError("stage", f"Shopify rejected staged images: {messages}")
        targets = tuple(getattr(payload, "stagedTargets", None) or ())
        if len(targets) != expected:
            raise ProductImageStageError("stage", "Shopify returned an unexpected staging target count")
        return targets

    def _upload(self, image: _NormalizedImage, target: object, index: int) -> StagedProductImage:
        """Upload one verified local file and return its temporary resource URL."""

        upload_url = getattr(target, "url", None)
        resource_url = getattr(target, "resourceUrl", None)
        if upload_url is None or resource_url is None:
            raise ProductImageStageError("stage", "Shopify returned an incomplete staging target")
        payload = image.path.read_bytes()
        if len(payload) != image.size_bytes:
            raise ProductImageStageError("read", "Local image changed before upload", image_index=index)
        parameters = getattr(target, "parameters", None) or ()
        headers = {str(item.name): str(item.value) for item in parameters}
        try:
            self._transport.put(str(upload_url), payload, headers)
        except ProductImageStageError:
            raise
        except Exception as exc:
            raise ProductImageStageError(
                "upload", "Shopify staged image upload failed", image_index=index
            ) from exc
        return StagedProductImage(
            original_source=AnyHttpUrl(str(resource_url)),
            filename=image.path.name,
            mime_type=image.mime_type,
            size_bytes=image.size_bytes,
            alt=image.alt,
        )

    @staticmethod
    def _normalize(image: LocalProductImage, index: int) -> _NormalizedImage:
        """Validate one immutable local image before requesting a staging target."""

        path = image.path
        if not path.is_file():
            raise ProductImageStageError("read", "Local image file does not exist", image_index=index)
        size = path.stat().st_size
        if size <= 0 or size > SHOPIFY_IMAGE_MAX_BYTES:
            raise ProductImageStageError("read", "Local image size is unsupported", image_index=index)
        mime_type = mimetypes.guess_type(path.name)[0]
        if mime_type not in _SUPPORTED_IMAGE_TYPES:
            raise ProductImageStageError("read", "Local image type is unsupported", image_index=index)
        return _NormalizedImage(
            path=path,
            alt=image.alt,
            mime_type=mime_type,
            size_bytes=size,
            input=StagedUploadInput(
                resource="IMAGE",
                filename=path.name,
                mimeType=mime_type,
                httpMethod="PUT",
                fileSize=size,
            ),
        )


class _NormalizedImage(BaseModel):
    """Internally validated local image plus typed stage input."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    path: Path
    alt: str | None
    mime_type: str
    size_bytes: int
    input: StagedUploadInput
