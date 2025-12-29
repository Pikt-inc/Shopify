from typing import Any, Iterator, Mapping
from functools import cached_property

from shopify_sdk import client as default_client
from shopify_sdk.gql.core.mutation import Mutation
from shopify_sdk.gql.core.types.payload import (
    BulkOperationRunMutationPayload,
    BulkOperationResultPayload,
)
from .chunker import iter_jsonl_chunks, JsonlChunk

MAX_JSONL_BYTES = 5 * 1024 * 1024  # 5 MB
UPLOAD_TIMEOUT_S = 300  # 5 minutes
DOWNLOAD_TIMEOUT_S = 300  # 5 minutes
POLL_INTERVAL_S = 5  # seconds


class BulkMutationRunner:
    def __init__(
        self,
        mutations: list["Mutation"],
        filename: str = "bulk-mutation.jsonl",
        mime_type: str = "text/jsonl",
        client=default_client,
    ):
        self._mutations = mutations
        self._filename = filename
        self._mime_type = mime_type
        self._client = client

    @cached_property
    def mutations(self) -> list["Mutation"]:
        """
        We need to validate that all mutations are of the same type and instantiated
        """
        if not self._mutations:
            raise ValueError("At least one mutation must be provided.")
        type_cls = type(self._mutations[0])
        for mutation in self._mutations:
            if not isinstance(mutation, type_cls):
                raise ValueError("All mutations must be of the same type.")

        for mutation in self._mutations:
            if not mutation.arguments:
                raise ValueError("All mutations must be instantiated with arguments.")
        return self._mutations

    @property
    def inner_mutation(self) -> str:
        return self.mutations[0].body

    @cached_property
    def variables(self) -> list[Mapping[str, Any]]:
        serialized_vars: list[Mapping[str, Any]] = []
        for mutation in self.mutations:
            variables = {
                name: mutation._serialize_value(value)
                for name, value in mutation._input_arguments.items()
            }
            serialized_vars.append(variables)
        return serialized_vars

    @property
    def chunks(
        self,
    ) -> Iterator[JsonlChunk]:
        for chunk in iter_jsonl_chunks(self.variables, max_bytes=MAX_JSONL_BYTES):
            yield chunk

    def run(
        self,
    ) -> Iterator[BulkOperationResultPayload]:
        return self._upload_chunks()

    def _upload_chunks(self) -> Iterator[BulkOperationResultPayload]:
        from .upload import JSONUploadManager

        for chunk in self.chunks:
            um = JSONUploadManager(
                content=chunk.content,
                filename=self._filename,
                mime_type=self._mime_type,
                client=self._client,
            )
            success = um.upload()
            if not success:
                raise ValueError(
                    f"Failed to upload chunk starting at line {chunk.start_line_index} JSONL data."
                )
            operation_id = self._start_mutation(
                staged_upload_path=um.staged_upload_path
            )
            from .poll import BulkActionResultManager as Poller

            for res_chunk in Poller.yield_results(
                bulk_operation_id=operation_id,
                client=self._client,
            ):
                yield res_chunk

    def _start_mutation(self, staged_upload_path: str) -> str:
        from shopify_sdk.gql.mutations import bulkOperationRunMutation

        response: BulkOperationRunMutationPayload = bulkOperationRunMutation(
            mutation=self.inner_mutation, stagedUploadPath=staged_upload_path
        ).execute(client=self._client)
        if not response.bulkOperation:
            raise ValueError("No bulk operation was created.")

        return response.bulkOperation.id
