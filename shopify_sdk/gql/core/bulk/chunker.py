from __future__ import annotations

import json
from typing import Any, Iterable, Iterator, Mapping
from pydantic import BaseModel

DEFAULT_MAX_JSONL_BYTES = 100_000_000


class JsonlChunk(BaseModel):
    content: bytes
    line_count: int
    start_line_index: int


def _json_line_bytes(line: Mapping[str, Any]) -> bytes:
    return (json.dumps(line, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


class JsonlChunker:
    """Produce JSONL chunks from an iterable of mapping objects.

    Usage:
        chunker = JsonlChunker(max_bytes=...)
        for chunk in chunker.iter_chunks(lines):
            ...
    """

    def __init__(self, *, max_bytes: int = DEFAULT_MAX_JSONL_BYTES) -> None:
        if max_bytes <= 0:
            raise ValueError("max_bytes must be > 0")
        self._max_bytes = max_bytes

    def iter_chunks(self, lines: Iterable[Mapping[str, Any]]) -> Iterator[JsonlChunk]:
        chunk = bytearray()
        start_line_index = 0
        line_count = 0

        for line_index, line in enumerate(lines):
            try:
                encoded = _json_line_bytes(line)
            except (TypeError, ValueError) as e:
                snippet = str(line)
                if len(snippet) > 200:
                    snippet = snippet[:200] + "...(truncated)"
                raise ValueError(f"Failed to JSON-encode JSONL line {line_index}: {e}; line={snippet}") from e
            if len(encoded) > self._max_bytes:
                raise ValueError(
                    f"JSONL line {line_index} is {len(encoded)} bytes, which exceeds max_bytes={self._max_bytes}."
                )

            if chunk and (len(chunk) + len(encoded) > self._max_bytes):
                yield JsonlChunk(
                    content=bytes(chunk),
                    line_count=line_count,
                    start_line_index=start_line_index,
                )
                chunk = bytearray()
                start_line_index = line_index
                line_count = 0

            chunk.extend(encoded)
            line_count += 1

        if chunk:
            yield JsonlChunk(
                content=bytes(chunk),
                line_count=line_count,
                start_line_index=start_line_index,
            )


def iter_jsonl_chunks(
    lines: Iterable[Mapping[str, Any]], *, max_bytes: int = DEFAULT_MAX_JSONL_BYTES
) -> Iterator[JsonlChunk]:
    return JsonlChunker(max_bytes=max_bytes).iter_chunks(lines)
