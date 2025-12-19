from __future__ import annotations

import inspect
import itertools
import logging
import json
from enum import Enum
from typing import Any, Iterable, Iterator, Mapping, Type

from pydantic import BaseModel, Field

from shopify_sdk import client as default_client
from shopify_sdk.gql.core import Mutation, Query
from shopify_sdk.gql.core.types.input_objects import input_object

from .operations import LogFn, run_bulk_mutation
from .operations import run_bulk_query as operations_run_bulk_query

logger = logging.getLogger(__name__)


class BulkOperationResult(BaseModel):
    index: int
    mutation: str
    success: bool
    user_errors: list[dict[str, Any]] = Field(default_factory=list)
    top_errors: list[Any] = Field(default_factory=list)
    payload: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None
    line_number: int | None = None


def _peek_first(iterable: Iterable[Any]) -> tuple[Any, Iterable[Any]]:
    iterator = iter(iterable)
    try:
        first = next(iterator)
    except StopIteration:
        raise ValueError("variables_iter is empty; cannot prepare bulk mutation.")
    return first, itertools.chain([first], iterator)


def _get_single_argument_name(mutation_cls: Type[Mutation]) -> str:
    sig = inspect.signature(mutation_cls.__init__)
    params = [
        p
        for name, p in sig.parameters.items()
        if name != "self" and p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
    ]
    if len(params) != 1:
        raise ValueError("Bulk mutations currently require exactly one argument.")
    return params[0].name


def _prepare_mutation(
    action: Mutation | Type[Mutation],
    variables_iter: Iterable[Any],
) -> tuple[Mutation, str, Iterable[Any]]:
    first_item, replayable_iter = _peek_first(variables_iter)

    if isinstance(action, Query):
        raise NotImplementedError(
            "Bulk queries are not supported by run_bulk_operation. Use run_bulk_query for Query instances."
        )
    if isinstance(action, type):
        if not issubclass(action, Mutation):
            raise TypeError("action class must be a Mutation subclass.")
        arg_name = _get_single_argument_name(action)
        mutation = action(**{arg_name: first_item})
    elif isinstance(action, Mutation):
        mutation = action
    else:
        raise TypeError("action must be a Mutation instance or Mutation class.")

    arg_names = list(mutation._input_arguments.keys())
    if len(arg_names) != 1:
        raise ValueError("Bulk mutations currently require exactly one argument.")
    return mutation, arg_names[0], replayable_iter


def _serialize_variable(arg_name: str, item: Any) -> Mapping[str, Any]:
    try:
        if hasattr(item, "to_graphql"):
            payload = item.to_graphql()
        elif isinstance(item, BaseModel):
            payload = item.model_dump(exclude_none=True)
        elif isinstance(item, Mapping):
            payload = dict(item)
        else:
            raise TypeError(f"Unsupported variable payload: {type(item).__name__}")
    except Exception as e:  # pragma: no cover - defensive
        raise ValueError(f"Failed to serialize variable for argument {arg_name!r}: {e}") from e
    return {arg_name: payload}


def _extract_payload(line: Any, mutation_name: str) -> dict[str, Any] | None:
    if not isinstance(line, dict):
        return None
    data = line.get("data")
    if isinstance(data, dict):
        op_payload = data.get(mutation_name)
        if isinstance(op_payload, dict):
            return op_payload
        return data
    op_payload = line.get(mutation_name)
    return op_payload if isinstance(op_payload, dict) else None


def _build_bulk_result(line: Any, mutation_name: str, index: int) -> BulkOperationResult:
    payload = _extract_payload(line, mutation_name)

    user_errors: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        raw_errors = payload.get("userErrors")
        if isinstance(raw_errors, list):
            user_errors = [e for e in raw_errors if isinstance(e, dict)]

    top_errors_raw = line.get("errors") if isinstance(line, dict) else None
    top_errors: list[Any] = top_errors_raw if isinstance(top_errors_raw, list) else []

    line_number = None
    if isinstance(line, dict):
        raw_line_number = line.get("__bulkGlobalLineNumber") or line.get("__lineNumber")
        if isinstance(raw_line_number, int):
            line_number = raw_line_number

    success = not user_errors and not top_errors
    return BulkOperationResult(
        index=index,
        mutation=mutation_name,
        success=success,
        user_errors=user_errors,
        top_errors=top_errors,
        payload=payload,
        raw=line if isinstance(line, dict) else None,
        line_number=line_number,
    )


def run_bulk_operation(
    action: Mutation | Type[Mutation],
    variables_iter: Iterable[input_object],
    *,
    client=default_client,
    verbose: bool = False,
    log: LogFn | None = None,
) -> Iterator[BulkOperationResult]:
    """
    Run a bulk mutation with the given variables, streaming structured results.

    The mutation must accept a single input argument; each item in variables_iter
    is serialized to that argument before being uploaded.

    For bulk queries, use ``run_bulk_query`` instead.
    """
    mutation, arg_name, variables = _prepare_mutation(action, variables_iter)
    log_fn = log or logger.info

    variable_lines = (_serialize_variable(arg_name, item) for item in variables)
    for index, line in enumerate(
        run_bulk_mutation(
            inner_mutation=mutation.body,
            variables=variable_lines,
            client=client,
            verbose=verbose,
            log=log_fn if verbose else None,
        ),
        start=1,
    ):
        yield _build_bulk_result(line, mutation.class_name, index)


def _format_graphql_literal(value: Any) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return "null"
    if isinstance(value, Mapping):
        inner = ", ".join(f"{str(k)}: {_format_graphql_literal(v)}" for k, v in value.items())
        return f"{{{inner}}}"
    if isinstance(value, list):
        inner = ", ".join(_format_graphql_literal(v) for v in value)
        return f"[{inner}]"
    return str(value)


def _inline_query_string(query: Query) -> str:
    args_list = query._input_arguments
    args_inline = ", ".join(f"{name}: {_format_graphql_literal(value)}" for name, value in args_list.items())

    spacer = " " * query._indent
    args_fragment = f"({args_inline})" if args_inline else ""
    return "\n".join(
        [
            "{",
            f"{spacer}{query.class_name}{args_fragment} {{",
            f"{query.fields}",
            f"{spacer}}}",
            "}",
        ]
    )


def run_bulk_query(
    query: Query | str,
    *,
    client=default_client,
    verbose: bool = False,
    log: LogFn | None = None,
) -> Iterator[dict[str, Any]]:
    """
    Run a bulk query (bulkOperationRunQuery) and stream raw JSONL results.

    Accepts either a pre-built GraphQL query string or a Query instance; the
    query must include at least one connection to be valid for bulk execution.
    """
    if isinstance(query, Query):
        query_str = _inline_query_string(query)
    elif isinstance(query, str):
        query_str = query
    else:
        raise TypeError("query must be a Query instance or a GraphQL query string.")

    log_fn = log or logger.info
    yield from operations_run_bulk_query(
        query=query_str,
        client=client,
        verbose=verbose,
        log=log_fn if verbose else None,
    )
