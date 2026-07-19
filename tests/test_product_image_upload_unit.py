"""Unit tests for typed local Shopify image staging."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from shopify_sdk.common.product.image_upload import (
    LocalProductImage,
    ProductImageStageError,
    ProductImageStager,
)


class _Transport:
    """Record signed uploads without making network requests."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, bytes, dict[str, str]]] = []

    def put(self, url: str, payload: bytes, headers: dict[str, str]) -> None:
        """Record one staged upload."""

        self.calls.append((url, payload, headers))


def _target(index: int) -> SimpleNamespace:
    """Build one typed-payload-compatible staging target stand-in."""

    return SimpleNamespace(
        url=f"https://signed-upload.example/{index}?secret=hidden",
        resourceUrl=f"https://shopify-staged.example/resource/{index}",
        parameters=[SimpleNamespace(name="Content-Type", value="image/jpeg")],
    )


def test_stages_ordered_local_images_and_returns_resource_urls(tmp_path: Path) -> None:
    first = tmp_path / "front.jpg"
    second = tmp_path / "back.jpg"
    first.write_bytes(b"front-image")
    second.write_bytes(b"back-image")
    captured_inputs: list[object] = []

    def stage(inputs: list[object]) -> SimpleNamespace:
        captured_inputs.extend(inputs)
        return SimpleNamespace(stagedTargets=[_target(1), _target(2)], userErrors=[])

    transport = _Transport()
    result = ProductImageStager(transport, stage).stage(
        [
            LocalProductImage(path=first, alt="Front"),
            LocalProductImage(path=second, alt="Back"),
        ]
    )

    assert [item.filename for item in result.images] == ["front.jpg", "back.jpg"]
    assert [str(item.original_source) for item in result.images] == [
        "https://shopify-staged.example/resource/1",
        "https://shopify-staged.example/resource/2",
    ]
    assert [item.resource for item in captured_inputs] == ["IMAGE", "IMAGE"]
    assert [item.httpMethod for item in captured_inputs] == ["PUT", "PUT"]
    assert [item.fileSize for item in captured_inputs] == [11, 10]
    assert [call[1] for call in transport.calls] == [b"front-image", b"back-image"]
    assert transport.calls[0][2] == {"Content-Type": "image/jpeg"}


def test_rejects_invalid_files_before_requesting_staging(tmp_path: Path) -> None:
    called = False

    def stage(_inputs: list[object]) -> object:
        nonlocal called
        called = True
        return object()

    with pytest.raises(ProductImageStageError, match="does not exist"):
        ProductImageStager(_Transport(), stage).stage(
            [LocalProductImage(path=tmp_path / "missing.jpg")]
        )
    assert called is False

    unsupported = tmp_path / "image.txt"
    unsupported.write_text("not an image")
    with pytest.raises(ProductImageStageError, match="type is unsupported"):
        ProductImageStager(_Transport(), stage).stage([LocalProductImage(path=unsupported)])
    assert called is False


def test_rejects_user_errors_without_exposing_signed_targets(tmp_path: Path) -> None:
    image = tmp_path / "front.png"
    image.write_bytes(b"png-image")
    transport = _Transport()

    def stage(_inputs: list[object]) -> SimpleNamespace:
        return SimpleNamespace(
            stagedTargets=[_target(1)],
            userErrors=[SimpleNamespace(message="invalid image")],
        )

    with pytest.raises(ProductImageStageError, match="invalid image") as caught:
        ProductImageStager(transport, stage).stage([LocalProductImage(path=image)])

    assert "signed-upload" not in str(caught.value)
    assert transport.calls == []


def test_detects_local_file_change_between_staging_and_upload(tmp_path: Path) -> None:
    image = tmp_path / "front.webp"
    image.write_bytes(b"first")

    def stage(_inputs: list[object]) -> SimpleNamespace:
        image.write_bytes(b"changed-size")
        return SimpleNamespace(stagedTargets=[_target(1)], userErrors=[])

    with pytest.raises(ProductImageStageError, match="changed before upload"):
        ProductImageStager(_Transport(), stage).stage([LocalProductImage(path=image)])


def test_empty_image_sequence_is_a_noop() -> None:
    result = ProductImageStager(_Transport(), lambda _inputs: object()).stage([])

    assert result.images == ()
