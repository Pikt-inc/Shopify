"""Retry policy and classification for safe Shopify Admin GraphQL reads."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .errors import ShopifyGraphQLError
from .errors import ShopifyHttpError
from .errors import ShopifyNetworkError
from .errors import ShopifyTransportError


class RequestRetryMode(StrEnum):
    """Describe whether a request is safe for automatic retry."""

    NEVER = "never"
    SAFE_READ = "safe_read"


class ShopifyRetryPolicy(BaseModel):
    """Starting retry defaults for idempotent Shopify Admin GraphQL reads."""

    max_attempts: int = Field(default=3, ge=1)
    initial_delay_seconds: float = Field(default=1.0, gt=0)
    maximum_delay_seconds: float = Field(default=8.0, gt=0)
    multiplier: float = Field(default=2.0, ge=1)
    jitter_ratio: float = Field(default=0.2, ge=0, le=1)
    retryable_status_codes: tuple[int, ...] = (429, 500, 502, 503, 504)
    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def validate_delay_bounds(self) -> "ShopifyRetryPolicy":
        """Ensure the maximum delay can accommodate the initial retry delay."""
        if self.maximum_delay_seconds < self.initial_delay_seconds:
            raise ValueError(
                "maximum_delay_seconds must be at least initial_delay_seconds."
            )
        return self


@dataclass(frozen=True)
class RetryDecision:
    """Describe a single retry delay and the condition that triggered it."""

    delay_seconds: float
    reason: str


class ShopifyRetryDecider:
    """Classify safe transient failures and calculate bounded retry delays."""

    def __init__(
        self,
        policy: ShopifyRetryPolicy,
        random_value: Callable[[], float],
    ) -> None:
        """Initialize policy state and the injectable jitter source."""
        self._policy = policy
        self._random_value = random_value

    def decide(
        self,
        error: ShopifyTransportError,
        retry_mode: RequestRetryMode,
        failed_attempt: int,
    ) -> RetryDecision | None:
        """Return a retry decision when a safe request failed transiently."""
        if retry_mode is not RequestRetryMode.SAFE_READ:
            return None
        if failed_attempt >= self._policy.max_attempts:
            return None
        if isinstance(error, ShopifyNetworkError):
            return self._backoff_decision(failed_attempt, "network")
        if isinstance(error, ShopifyHttpError) and self._is_retryable_status(error):
            return self._http_decision(error, failed_attempt)
        if isinstance(error, ShopifyGraphQLError) and error.is_throttled:
            return self._throttle_decision(error, failed_attempt)
        return None

    def _is_retryable_status(self, error: ShopifyHttpError) -> bool:
        """Return whether the HTTP status represents a documented temporary failure."""
        return error.status_code in self._policy.retryable_status_codes

    def _http_decision(
        self,
        error: ShopifyHttpError,
        failed_attempt: int,
    ) -> RetryDecision:
        """Honor a numeric Retry-After header before applying exponential backoff."""
        retry_after = self._retry_after_delay(error.retry_after)
        if retry_after is not None:
            return RetryDecision(delay_seconds=retry_after, reason="retry_after")
        return self._backoff_decision(failed_attempt, f"http_{error.status_code}")

    def _throttle_decision(
        self,
        error: ShopifyGraphQLError,
        failed_attempt: int,
    ) -> RetryDecision:
        """Use Shopify cost metadata when it implies a longer throttle recovery wait."""
        throttle_delay = self._throttle_delay(error)
        if throttle_delay is not None:
            return RetryDecision(delay_seconds=throttle_delay, reason="throttled_cost")
        return self._backoff_decision(failed_attempt, "throttled")

    def _backoff_decision(
        self,
        failed_attempt: int,
        reason: str,
    ) -> RetryDecision:
        """Calculate jittered exponential backoff for a failed attempt."""
        unjittered_delay = min(
            self._policy.maximum_delay_seconds,
            self._policy.initial_delay_seconds
            * self._policy.multiplier ** (failed_attempt - 1),
        )
        return RetryDecision(
            delay_seconds=self._jittered_delay(unjittered_delay),
            reason=reason,
        )

    def _jittered_delay(self, delay_seconds: float) -> float:
        """Apply symmetric bounded jitter to an exponential retry delay."""
        if self._policy.jitter_ratio == 0:
            return delay_seconds
        random_value = self._random_value()
        bounded_random_value = min(max(random_value, 0.0), 1.0)
        jitter = (bounded_random_value * 2 - 1) * self._policy.jitter_ratio
        return delay_seconds * (1 + jitter)

    @staticmethod
    def _retry_after_delay(retry_after: str | None) -> float | None:
        """Parse a non-negative numeric Retry-After value supplied by Shopify."""
        if retry_after is None:
            return None
        try:
            delay_seconds = float(retry_after)
        except ValueError:
            return None
        if not isfinite(delay_seconds) or delay_seconds < 0:
            return None
        return delay_seconds

    @staticmethod
    def _throttle_delay(error: ShopifyGraphQLError) -> float | None:
        """Calculate seconds needed to restore Shopify's requested query cost."""
        cost = error.cost
        if cost is None or cost.throttle_status is None:
            return None
        requested_cost = cost.requested_query_cost
        throttle_status = cost.throttle_status
        if requested_cost is None or throttle_status.restore_rate <= 0:
            return None
        deficit = requested_cost - throttle_status.currently_available
        if deficit <= 0:
            return None
        return deficit / throttle_status.restore_rate


def is_throttled_graphql_error(errors: list[object]) -> bool:
    """Return whether Shopify marked any top-level GraphQL error as throttled."""
    for error in errors:
        if not isinstance(error, Mapping):
            continue
        extensions = error.get("extensions")
        if not isinstance(extensions, Mapping):
            continue
        code = extensions.get("code")
        if isinstance(code, str) and code.upper() == "THROTTLED":
            return True
    return False
