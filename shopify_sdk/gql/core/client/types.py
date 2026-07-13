from pydantic import BaseModel, Field


class GQLRequestParams(BaseModel):
    query: str
    variables: dict[str, object] | None


class GQLThrottleStatus(BaseModel):
    maximum_available: int = Field(..., alias="maximumAvailable")
    currently_available: int = Field(..., alias="currentlyAvailable")
    restore_rate: int = Field(..., alias="restoreRate")


class GQLCost(BaseModel):
    requested_query_cost: int | None = Field(default=None, alias="requestedQueryCost")
    actual_query_cost: int | None = Field(default=None, alias="actualQueryCost")
    throttle_status: GQLThrottleStatus | None = Field(
        default=None,
        alias="throttleStatus",
    )


class GQLExtensions(BaseModel):
    cost: GQLCost | None = Field(default=None)


class GQLResponse(BaseModel):
    data: dict[str, object] | None = Field(default=None)
    extensions: GQLExtensions | None = Field(default=None)
