from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Iterator, Mapping, cast
from urllib.parse import urlparse

import requests
from requests.exceptions import RequestException

from shopify_sdk import client as default_client
from shopify_sdk.gql import bulkOperation as bulkOperationQuery
from shopify_sdk.gql import bulkOperationRunMutation, bulkOperationRunQuery, stagedUploadsCreate
from shopify_sdk.gql.core.types import BulkOperation, ID
from shopify_sdk.gql.core.types.input_objects import StagedUploadInput

logger = logging.getLogger(__name__)

DEFAULT_MAX_JSONL_BYTES = 100_000_000
DEFAULT_HTTP_TIMEOUT_S = 60.0 * 10
DEFAULT_BULK_TIMEOUT_S = 60.0 * 60 * 2  # default 2 hours to accommodate large operations
DEFAULT_BULK_POLL_INTERVAL_S = 2.0

LogFn = Callable[[str], None]


@dataclass(frozen=True, slots=True)
class StagedUploadTarget:
    upload_url: str
    resource_url: str
    parameters: dict[str, str]
    staged_upload_path: str


def _emit(
    verbose: bool,
    log: LogFn | None,
    message: str,
    *,
    level: int = logging.INFO,
) -> None:
    if not verbose:
        return
    if log is not None:
        log(message)
        return
    logger.log(level, message)


def _display_url(url: str, *, redact: bool) -> str:
    if not redact:
        return url
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    return url.split("?", 1)[0]


def _json_line_bytes(line: Mapping[str, Any]) -> bytes:
    return (json.dumps(line, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def build_jsonl_bytes(lines: Iterable[Mapping[str, Any]]) -> bytes:
    content = bytearray()
    for line_index, line in enumerate(lines):
        try:
            content.extend(_json_line_bytes(line))
        except (TypeError, ValueError) as e:
            snippet = str(line)
            if len(snippet) > 200:
                snippet = snippet[:200] + "...(truncated)"
            raise ValueError(f"Failed to JSON-encode JSONL line {line_index}: {e}; line={snippet}") from e
    return bytes(content)


@dataclass(frozen=True, slots=True)
class JsonlChunk:
    content: bytes
    line_count: int
    start_line_index: int


def iter_jsonl_chunks(
    lines: Iterable[Mapping[str, Any]],
    *,
    max_bytes: int = DEFAULT_MAX_JSONL_BYTES,
) -> Iterator[JsonlChunk]:
    if max_bytes <= 0:
        raise ValueError("max_bytes must be > 0")

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
        if len(encoded) > max_bytes:
            raise ValueError(
                f"JSONL line {line_index} is {len(encoded)} bytes, which exceeds max_bytes={max_bytes}."
            )

        if chunk and (len(chunk) + len(encoded) > max_bytes):
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


def _chunk_filename(filename: str, chunk_index: int) -> str:
    """Return a 1-based chunk filename, preserving suffix if present."""
    if chunk_index < 1:
        raise ValueError("chunk_index must be >= 1")
    stem, dot, suffix = filename.rpartition(".")
    if dot:
        return f"{stem}-{chunk_index:04d}.{suffix}"
    return f"{filename}-{chunk_index:04d}"


def _derive_staged_upload_path(resource_url: str) -> str:
    if resource_url.startswith("http://") or resource_url.startswith("https://"):
        path = urlparse(resource_url).path.lstrip("/")
    else:
        path = resource_url.lstrip("/")

    # Shopify may return a resourceUrl scoped under a "bulk/" bucket prefix,
    # while bulkOperationRunMutation expects the underlying object key (e.g. "tmp/uploads/...").
    if path.startswith("bulk/"):
        path = path.removeprefix("bulk/")
    return path


def stage_and_upload_jsonl(
    content: bytes,
    *,
    filename: str,
    mime_type: str = "text/jsonl",
    client=default_client,
    upload_timeout_s: float = DEFAULT_HTTP_TIMEOUT_S,
    session: requests.Session | None = None,
    redact_urls: bool = True,
    verbose: bool = False,
    log: LogFn | None = None,
) -> StagedUploadTarget:
    started = time.monotonic()
    _emit(
        verbose,
        log,
        f"[bulk] staging upload: filename={filename!r} bytes={len(content)} mime_type={mime_type!r}",
    )

    staged = stagedUploadsCreate(
        input=[
            StagedUploadInput(
                resource="BULK_MUTATION_VARIABLES",
                filename=filename,
                mimeType=mime_type,
                httpMethod="POST",
                fileSize=len(content),
            )
        ]
    ).execute(client=client)

    targets = staged.get("stagedTargets")
    if not isinstance(targets, list) or not targets:
        raise ValueError("stagedUploadsCreate returned no stagedTargets.")
    target = targets[0]
    if not isinstance(target, dict):
        raise TypeError("stagedUploadsCreate stagedTargets[0] is not a dict.")

    upload_url = target.get("url")
    resource_url = target.get("resourceUrl")
    if not isinstance(upload_url, str) or not isinstance(resource_url, str):
        raise ValueError("stagedUploadsCreate returned invalid stagedTargets url/resourceUrl.")

    params: dict[str, str] = {}
    raw_params = target.get("parameters", [])
    if isinstance(raw_params, list):
        for param in raw_params:
            if not isinstance(param, dict):
                continue
            name = param.get("name")
            value = param.get("value")
            if isinstance(name, str) and isinstance(value, str):
                params[name] = value

    if params.get("key"):
        key_info = f"key={params.get('key')}"
    else:
        key_info = f"params_keys={sorted(params.keys())}"
    display_upload_url = _display_url(upload_url, redact=redact_urls)
    display_resource_url = _display_url(resource_url, redact=redact_urls)
    _emit(
        verbose,
        log,
        "[bulk] stagedUploadsCreate target:"
        f" upload_url={display_upload_url}"
        f" resource_url={display_resource_url}"
        f" {key_info}",
    )

    http_post = session.post if session else requests.post
    response = None
    try:
        response = http_post(
            upload_url,
            data=params,
            files={"file": (filename, content, mime_type)},
            timeout=upload_timeout_s,
        )
        _emit(verbose, log, f"[bulk] staged upload response: status_code={response.status_code}")
        if response.status_code not in (200, 201, 204):
            raise ValueError(
                f"Staged upload failed with status {response.status_code}: {response.text[:500]}"
            )
    except RequestException as e:
        raise ValueError(f"Staged upload POST failed to {display_upload_url}: {e}") from e
    finally:
        if response is not None:
            response.close()

    staged_upload_path = params.get("key") or _derive_staged_upload_path(resource_url)
    _emit(
        verbose,
        log,
        f"[bulk] staged upload complete: staged_upload_path={staged_upload_path}",
    )
    _emit(verbose, log, f"[bulk] staged upload duration_s={time.monotonic() - started:.2f}")
    return StagedUploadTarget(
        upload_url=upload_url,
        resource_url=resource_url,
        parameters=params,
        staged_upload_path=staged_upload_path,
    )


def start_bulk_mutation(
    *,
    inner_mutation: str,
    staged_upload_path: str,
    client=default_client,
    verbose: bool = False,
    log: LogFn | None = None,
) -> ID:
    first_line = inner_mutation.strip().splitlines()[0] if inner_mutation.strip() else ""
    _emit(
        verbose,
        log,
        f"[bulk] starting bulk mutation: stagedUploadPath={staged_upload_path} inner={first_line[:200]}",
    )

    payload = bulkOperationRunMutation(
        mutation=inner_mutation,
        stagedUploadPath=staged_upload_path,
    ).execute(client=client)

    bulk_op = payload.get("bulkOperation", {})
    if not isinstance(bulk_op, dict):
        raise TypeError("bulkOperationRunMutation bulkOperation is not a dict.")
    bulk_operation_id = bulk_op.get("id")
    if not isinstance(bulk_operation_id, str):
        raise ValueError("bulkOperationRunMutation returned no bulkOperation.id.")
    _emit(
        verbose,
        log,
        f"[bulk] bulk operation started: id={bulk_operation_id} status={bulk_op.get('status')}",
    )
    return bulk_operation_id


def start_bulk_query(
    *,
    query: str,
    client=default_client,
    verbose: bool = False,
    log: LogFn | None = None,
) -> ID:
    trimmed = query.strip()
    if not trimmed:
        raise ValueError("bulk query must be a non-empty GraphQL query string.")
    first_line = trimmed.splitlines()[0]
    _emit(verbose, log, f"[bulk] starting bulk query: inner={first_line[:200]}")

    payload = bulkOperationRunQuery(query=trimmed).execute(client=client)
    if payload is None:
        raise ValueError("bulkOperationRunQuery returned no payload.")

    bulk_op = payload.get("bulkOperation", {})
    if not isinstance(bulk_op, dict):
        raise TypeError("bulkOperationRunQuery bulkOperation is not a dict.")
    bulk_operation_id = bulk_op.get("id")
    if not isinstance(bulk_operation_id, str):
        raise ValueError("bulkOperationRunQuery returned no bulkOperation.id.")
    _emit(
        verbose,
        log,
        f"[bulk] bulk query started: id={bulk_operation_id} status={bulk_op.get('status')}",
    )
    return bulk_operation_id


def get_bulk_operation(
    bulk_operation_id: ID,
    *,
    client=default_client,
) -> BulkOperation:
    operation = bulkOperationQuery(id=bulk_operation_id).execute(client=client)
    if operation is None:
        raise ValueError(f"No bulk operation found for id={bulk_operation_id!r}.")
    return cast(BulkOperation, operation)


def wait_for_bulk_operation(
    bulk_operation_id: ID,
    *,
    client=default_client,
    poll_interval_s: float = DEFAULT_BULK_POLL_INTERVAL_S,
    timeout_s: float = DEFAULT_BULK_TIMEOUT_S,
    redact_urls: bool = True,
    verbose: bool = False,
    log: LogFn | None = None,
) -> BulkOperation:
    """
    Poll a bulk operation until it reaches a terminal status or the timeout expires.

    The default timeout is intentionally long (2 hours) to allow large jobs to finish.
    If you expect smaller operations, pass a shorter ``timeout_s`` to avoid waiting
    too long when an operation is stuck in a non-terminal state.
    """
    terminal_statuses = {"COMPLETED", "FAILED", "CANCELED", "CANCELLED", "EXPIRED"}
    deadline = time.monotonic() + timeout_s
    last_snapshot: tuple[str | None, Any, str | None, str | None, str | None] | None = None

    while True:
        operation = get_bulk_operation(bulk_operation_id, client=client)
        status = (operation.status or "").upper()
        if verbose:
            snapshot = (
                operation.status,
                operation.objectCount,
                operation.errorCode,
                _display_url(operation.url, redact=redact_urls) if operation.url else None,
                _display_url(operation.partialDataUrl, redact=redact_urls)
                if operation.partialDataUrl
                else None,
            )
            if snapshot != last_snapshot:
                _emit(
                    verbose,
                    log,
                    "[bulk] status:"
                    f" id={bulk_operation_id}"
                    f" status={operation.status!r}"
                    f" objectCount={operation.objectCount!r}"
                    f" errorCode={operation.errorCode!r}"
                    f" url={snapshot[3]!r}"
                    f" partialDataUrl={snapshot[4]!r}",
                )
                last_snapshot = snapshot
        if status in terminal_statuses:
            return operation
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"Bulk operation {bulk_operation_id} did not complete within {timeout_s} seconds; last status={operation.status!r}."
            )
        time.sleep(poll_interval_s)


def iter_bulk_operation_results(
    results_url: str,
    *,
    timeout_s: float = DEFAULT_HTTP_TIMEOUT_S,
    session: requests.Session | None = None,
    redact_urls: bool = True,
    verbose: bool = False,
    log: LogFn | None = None,
) -> Iterator[dict[str, Any]]:
    display_url = _display_url(results_url, redact=redact_urls)
    _emit(verbose, log, f"[bulk] downloading results: url={display_url}")

    http = session or requests
    response = None
    try:
        response = http.get(results_url, stream=True, timeout=timeout_s)
        response.raise_for_status()

        for line_number, line in enumerate(response.iter_lines(decode_unicode=True), start=1):
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                snippet = line[:500]
                raise ValueError(
                    f"Invalid JSON in bulk results from {display_url} at line {line_number}: {snippet}"
                ) from e
    except RequestException as e:
        raise ValueError(f"Failed to download bulk results from {display_url}: {e}") from e
    finally:
        if response is not None:
            response.close()


def run_bulk_mutation(
    *,
    inner_mutation: str,
    variables: Iterable[Mapping[str, Any]],
    filename: str = "bulk-mutation.jsonl",
    mime_type: str = "text/jsonl",
    client=default_client,
    max_jsonl_bytes: int = DEFAULT_MAX_JSONL_BYTES,
    poll_interval_s: float = DEFAULT_BULK_POLL_INTERVAL_S,
    timeout_s: float = DEFAULT_BULK_TIMEOUT_S,
    upload_timeout_s: float = DEFAULT_HTTP_TIMEOUT_S,
    download_timeout_s: float = DEFAULT_HTTP_TIMEOUT_S,
    session: requests.Session | None = None,
    redact_urls: bool = True,
    allow_partial_results: bool = False,
    verbose: bool = False,
    log: LogFn | None = None,
) -> Iterator[dict[str, Any]]:
    if not inner_mutation.strip():
        raise ValueError("inner_mutation must be a non-empty GraphQL mutation string.")

    started = time.monotonic()
    total_results = 0
    chunks_run = 0

    for chunk_index, chunk in enumerate(iter_jsonl_chunks(variables, max_bytes=max_jsonl_bytes), start=1):
        chunks_run += 1
        chunk_started = time.monotonic()
        _emit(
            verbose,
            log,
            f"[bulk] chunk {chunk_index:04d}: lines={chunk.line_count} bytes={len(chunk.content)} start_line={chunk.start_line_index}",
        )

        staged = stage_and_upload_jsonl(
            chunk.content,
            filename=_chunk_filename(filename, chunk_index),
            mime_type=mime_type,
            client=client,
            upload_timeout_s=upload_timeout_s,
            session=session,
            redact_urls=redact_urls,
            verbose=verbose,
            log=log,
        )
        bulk_operation_id = start_bulk_mutation(
            inner_mutation=inner_mutation,
            staged_upload_path=staged.staged_upload_path,
            client=client,
            verbose=verbose,
            log=log,
        )
        operation = wait_for_bulk_operation(
            bulk_operation_id,
            client=client,
            poll_interval_s=poll_interval_s,
            timeout_s=timeout_s,
            redact_urls=redact_urls,
            verbose=verbose,
            log=log,
        )

        status_upper = (operation.status or "").upper()
        results_url: str | None = None

        if status_upper == "COMPLETED":
            results_url = operation.url
            if not results_url:
                raise ValueError(
                    "Bulk operation completed without a results url;"
                    f" id={bulk_operation_id!r} status={operation.status!r} errorCode={operation.errorCode!r}."
                )
        else:
            if allow_partial_results and operation.partialDataUrl:
                results_url = operation.partialDataUrl
                _emit(
                    verbose,
                    log,
                    f"[bulk] chunk {chunk_index:04d} finished with status={operation.status!r}; using partialDataUrl.",
                    level=logging.WARNING,
                )
            else:
                raise ValueError(
                    "Bulk operation did not complete successfully and has no usable results url;"
                    f" id={bulk_operation_id!r} status={operation.status!r} errorCode={operation.errorCode!r}."
                )

        display_results_url = _display_url(results_url, redact=redact_urls)
        _emit(
            verbose,
            log,
            f"[bulk] chunk {chunk_index:04d} completed: id={bulk_operation_id} status={operation.status!r} url={display_results_url} run_s={time.monotonic() - chunk_started:.2f}",
        )

        download_started = time.monotonic()
        chunk_results = 0
        for result in iter_bulk_operation_results(
            results_url,
            timeout_s=download_timeout_s,
            session=session,
            redact_urls=redact_urls,
            verbose=verbose,
            log=log,
        ):
            if isinstance(result, dict):
                result.setdefault("__bulkOperationId", bulk_operation_id)
                result.setdefault("__bulkChunkIndex", chunk_index)
                result.setdefault("__bulkChunkStartLine", chunk.start_line_index)
                line_number = result.get("__lineNumber")
                if isinstance(line_number, int):
                    result.setdefault("__bulkGlobalLineNumber", chunk.start_line_index + line_number)
            chunk_results += 1
            total_results += 1
            yield result

        _emit(
            verbose,
            log,
            f"[bulk] chunk {chunk_index:04d} results downloaded: count={chunk_results} download_s={time.monotonic() - download_started:.2f}",
        )

    _emit(
        verbose,
        log,
        f"[bulk] finished: chunks={chunks_run} results={total_results} duration_s={time.monotonic() - started:.2f}",
    )


def run_bulk_query(
    *,
    query: str,
    client=default_client,
    poll_interval_s: float = DEFAULT_BULK_POLL_INTERVAL_S,
    timeout_s: float = DEFAULT_BULK_TIMEOUT_S,
    download_timeout_s: float = DEFAULT_HTTP_TIMEOUT_S,
    session: requests.Session | None = None,
    redact_urls: bool = True,
    verbose: bool = False,
    log: LogFn | None = None,
) -> Iterator[dict[str, Any]]:
    trimmed = query.strip()
    if not trimmed:
        raise ValueError("query must be a non-empty GraphQL query string.")

    started = time.monotonic()
    _emit(verbose, log, "[bulk] starting bulk query operation")

    bulk_operation_id = start_bulk_query(
        query=trimmed,
        client=client,
        verbose=verbose,
        log=log,
    )
    operation = wait_for_bulk_operation(
        bulk_operation_id,
        client=client,
        poll_interval_s=poll_interval_s,
        timeout_s=timeout_s,
        redact_urls=redact_urls,
        verbose=verbose,
        log=log,
    )

    status_upper = (operation.status or "").upper()
    if status_upper != "COMPLETED":
        raise ValueError(
            "Bulk query did not complete successfully;"
            f" id={bulk_operation_id!r} status={operation.status!r} errorCode={operation.errorCode!r}."
        )
    results_url = operation.url
    if not results_url:
        raise ValueError(
            "Bulk query completed without a results url;"
            f" id={bulk_operation_id!r} status={operation.status!r} errorCode={operation.errorCode!r}."
        )

    display_results_url = _display_url(results_url, redact=redact_urls)
    _emit(
        verbose,
        log,
        f"[bulk] bulk query completed: id={bulk_operation_id} status={operation.status!r} url={display_results_url}",
    )

    download_started = time.monotonic()
    total_results = 0
    for result in iter_bulk_operation_results(
        results_url,
        timeout_s=download_timeout_s,
        session=session,
        redact_urls=redact_urls,
        verbose=verbose,
        log=log,
    ):
        if isinstance(result, dict):
            result.setdefault("__bulkOperationId", bulk_operation_id)
            result.setdefault("__bulkChunkIndex", 1)
            result.setdefault("__bulkChunkStartLine", 0)
            line_number = result.get("__lineNumber")
            if isinstance(line_number, int):
                result.setdefault("__bulkGlobalLineNumber", line_number)
        total_results += 1
        yield result

    _emit(
        verbose,
        log,
        f"[bulk] bulk query results downloaded: count={total_results} download_s={time.monotonic() - download_started:.2f}",
    )
    _emit(
        verbose,
        log,
        f"[bulk] bulk query finished: results={total_results} duration_s={time.monotonic() - started:.2f}",
    )
