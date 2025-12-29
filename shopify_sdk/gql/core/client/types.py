from pydantic import BaseModel, Field


class GQLRequestParams(BaseModel):
    query: str
    variables: dict | None


class GQLThrottleStatus(BaseModel):
    maximum_available: int = Field(..., alias="maximumAvailable")
    currently_available: int = Field(..., alias="currentlyAvailable")
    restore_rate: int = Field(..., alias="restoreRate")


class GQLCost(BaseModel):
    requested_query_cost: int = Field(..., alias="requestedQueryCost")
    actual_query_cost: int = Field(..., alias="actualQueryCost")
    throttle_status: GQLThrottleStatus = Field(..., alias="throttleStatus")


class GQLExtensions(BaseModel):
    cost: GQLCost


class GQLResponse(BaseModel):
    data: dict | None
    extensions: GQLExtensions | None
