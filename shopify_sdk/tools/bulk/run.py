from __future__ import annotations

import inspect
import itertools
import logging
from typing import Any, Iterable, Iterator, Mapping, Type

from pydantic import BaseModel, Field

from shopify_sdk import client as default_client
from shopify_sdk.gql.core import Mutation, Query
from shopify_sdk.gql.core.types.input_objects import input_object

from .operations import LogFn, _run_bulk_mutation
from .operations import run_bulk_query as operations_run_bulk_query

logger = logging.getLogger(__name__)


class BulkOperationResult(BaseModel):
    index: int
    mutation: str
    success: bool
    user_errors: list[dict[str, Any]] = Field(default_factory=list)
    top_errors: list[Any] = Field(default_factory=list)
    payload: Mapping[str, Any] | None = Field(
        default=None,
        description=(
            "The extracted, mutation-specific data for this bulk operation line. "
            "Typically a subset of `raw` under the mutation root; may be None when "
            "no payload could be extracted (e.g., only errors present)."
        ),
    )
    raw: dict[str, Any] | None = Field(
        default=None,
        description=(
            "The full parsed JSON object for the bulk operation line as returned by Shopify. "
            "Use primarily for debugging or advanced inspection; prefer `payload` for normal use."
        ),
    )
    data: Mapping[str, Any] | None = None
    line_number: int | None = None


def _peek_first(iterable: Iterable[input_object]) -> tuple[input_object, Iterable[input_object]]:
    iterator = iter(iterable)
    try:
        first = next(iterator)
    except StopIteration:
        raise ValueError("variables_iter is empty; cannot prepare bulk mutation.")
    return first, itertools.chain([first], iterator)


def _get_argument_names(mutation_cls: Type[Mutation]) -> list[str]:
    sig = inspect.signature(mutation_cls.__init__)
    params = [
        p
        for name, p in sig.parameters.items()
        if name != "self" and p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
    ]
    if not params:
        raise ValueError(
            "Bulk mutation __init__ must declare at least one parameter (excluding self) for bulk execution."
        )
    return [p.name for p in params]


def _prepare_mutation(
    action: Mutation | Type[Mutation],
    variables_iter: Iterable[input_object],
) -> tuple[Mutation, list[str], Iterable[input_object]]:
    if isinstance(action, Mutation):
        # Handle concrete Mutation instances first; Mutation is a subclass of Query.
        _, replayable_iter = _peek_first(variables_iter)
        mutation = action
    elif isinstance(action, type):
        if issubclass(action, Mutation):
            first_item, replayable_iter = _peek_first(variables_iter)
            arg_names = _get_argument_names(action)
            if len(arg_names) == 1:
                mutation = action(**{arg_names[0]: first_item})
            else:
                if isinstance(first_item, Mapping):
                    kwargs = dict(first_item)
                elif isinstance(first_item, (list, tuple)):
                    if len(first_item) != len(arg_names):
                        raise ValueError(
                            "Iterable provided for bulk variables does not match mutation argument count."
                        )
                    kwargs = dict(zip(arg_names, first_item))
                else:
                    raise TypeError(
                        "For mutations with multiple input args, each variables item must be a mapping or sequence matching the argument names."
                    )
                mutation = action(**kwargs)
        elif issubclass(action, Query):
            raise NotImplementedError(
                "Bulk queries are not supported by run_bulk_mutation. Use run_bulk_query for Query instances."
            )
        else:
            raise TypeError("action class must be a Mutation subclass.")
    elif isinstance(action, Query):
        raise NotImplementedError(
            "Bulk queries are not supported by run_bulk_mutation. Use run_bulk_query for Query instances."
        )
    else:
        raise TypeError("action must be a Mutation instance or Mutation class.")

    arg_names = list(mutation._input_arguments.keys())
    if not arg_names:
        raise ValueError(
            "Bulk mutation instance must expose at least one input argument for bulk execution."
        )
    return mutation, arg_names, replayable_iter


def _serialize_variable(arg_names: list[str], item: Any, defaults: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
    def _to_payload(val: Any) -> Any:
        if hasattr(val, "to_graphql"):
            try:
                return val.to_graphql()
            except Exception as e:
                raise ValueError(f"Failed to serialize value to graphql: {e}") from e
        if isinstance(val, Mapping):
            return dict(val)
        return val

    if len(arg_names) == 1:
        try:
            payload = _to_payload(item)
        except Exception as e:
            item_type = type(item).__name__
            raise ValueError(
                f"Failed to serialize variable for argument {arg_names[0]!r} "
                f"with item of type {item_type}. Original error: {e}"
            ) from e
        return {arg_names[0]: payload}

    # Multiple arg names: accept Mapping[str, value] or sequence of values
    if isinstance(item, Mapping):
        out: dict[str, Any] = {}
        for name in arg_names:
            if name in item:
                out[name] = _to_payload(item[name])
            else:
                if defaults is not None and name in defaults:
                    out[name] = _to_payload(defaults[name])
                else:
                    raise ValueError(f"Missing argument {name!r} in variables mapping.")
        return out

    if isinstance(item, (list, tuple)):
        if len(item) != len(arg_names):
            raise ValueError("Variables sequence length does not match mutation argument count.")
        return {name: _to_payload(val) for name, val in zip(arg_names, item)}

    raise TypeError(
        "For mutations with multiple input args, each variables item must be a mapping or sequence matching the argument names."
    )


def _extract_payload(line: Mapping[str, Any], mutation_name: str) -> Mapping[str, Any] | None:
    if not isinstance(line, Mapping):
        return None
    op_payload = line.get(mutation_name)
    if isinstance(op_payload, dict):
        return op_payload

    data = line.get("data")
    if isinstance(data, dict):
        op_payload = data.get(mutation_name)
        if isinstance(op_payload, dict):
            return op_payload
        if "userErrors" in data:
            return data
        return None

    if "userErrors" in line:
        return line
    return None


def _build_bulk_result(line: Mapping[str, Any], mutation_name: str, index: int) -> BulkOperationResult:
    payload = _extract_payload(line, mutation_name)
    data = line.get("data", None)

    user_errors: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        raw_errors = payload.get("userErrors")
        if isinstance(raw_errors, list):
            user_errors = [e for e in raw_errors if isinstance(e, dict)]

    top_errors_raw = line.get("errors")
    top_errors: list[Any] = top_errors_raw if isinstance(top_errors_raw, list) else []

    line_number = None
    raw_line_number = line.get("__bulkGlobalLineNumber") or line.get("__lineNumber")
    if isinstance(raw_line_number, int):
        line_number = raw_line_number

    success = payload is not None and not user_errors and not top_errors
    return BulkOperationResult(
        index=index,
        mutation=mutation_name,
        success=success,
        user_errors=user_errors,
        top_errors=top_errors,
        payload=payload,
        data=data,
        raw=dict(line),
        line_number=line_number,
    )


def run_bulk_mutation(
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

    Use this helper for bulk write operations (create/update/delete) via Shopify's
    bulk mutation API. For read-only bulk exports that fetch data via connections,
    use ``run_bulk_query`` instead. Chunk failures abort iteration; per-item errors
    are surfaced on each ``BulkOperationResult`` instance.
    """
    mutation, arg_names, variables = _prepare_mutation(action, variables_iter)
    log_fn = log or logger.info

    variable_lines = (
        _serialize_variable(arg_names, item, defaults=mutation._input_arguments)
        for item in variables
    )
    for index, line in enumerate(
        _run_bulk_mutation(
            inner_mutation=mutation.body,
            variables=variable_lines,
            client=client,
            verbose=verbose,
            log=log_fn if verbose else None,
        ),
        start=1,
    ):
        yield _build_bulk_result(line, mutation.class_name, index)

def bulk_mutation(
    mutation: Mutation | Type[Mutation],
    mutation_body: str,
    variables: Iterable[str],
):
    for index, line in enumerate(
        _run_bulk_mutation(
            inner_mutation=mutation_body,
            variables=variables,
            client=default_client,
            verbose=True
        ),
        start=1,
    ):
        print(line)
        yield _build_bulk_result(line, mutation.class_name, index)


def run_bulk_query(
    query: Query | str,
    *,
    client=default_client,
    verbose: bool = False,
    log: LogFn | None = None,
) -> Iterator[dict[str, Any]]:
    """
    Run a bulk query (bulkOperationRunQuery) and stream raw JSONL results.

    Use this for read-only bulk exports that fetch data via connections. Accepts
    either a pre-built GraphQL query string or a Query instance; the query must
    include at least one connection to be valid for bulk execution. The helper
    raises if the bulk operation fails; per-line parsing errors surface during
    iteration.
    """
    if isinstance(query, Query):
        query_str = query.inline_body()
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
