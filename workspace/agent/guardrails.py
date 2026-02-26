from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(slots=True)
class RateLimitStats:
    wait_events: int = 0
    waited_seconds: float = 0.0
    batch_cooldowns: int = 0


class MinIntervalLimiter:
    def __init__(self, min_interval_seconds: float) -> None:
        self._min_interval_seconds = min_interval_seconds
        self._last_call_time: float | None = None

    def wait(self) -> float:
        if self._last_call_time is None:
            self._last_call_time = time.monotonic()
            return 0.0

        elapsed = time.monotonic() - self._last_call_time
        if elapsed >= self._min_interval_seconds:
            self._last_call_time = time.monotonic()
            return 0.0

        remaining = self._min_interval_seconds - elapsed
        time.sleep(remaining)
        self._last_call_time = time.monotonic()
        return remaining


class SearchBatchLimiter:
    def __init__(self, max_per_batch: int, cooldown_seconds: int) -> None:
        self._max_per_batch = max_per_batch
        self._cooldown_seconds = cooldown_seconds
        self._count = 0

    def before_next_search(self) -> bool:
        if self._count and self._count % self._max_per_batch == 0:
            time.sleep(self._cooldown_seconds)
            self._count += 1
            return True

        self._count += 1
        return False


class BudgetTracker:
    def __init__(
        self,
        daily_budget_usd: float,
        monthly_budget_usd: float,
        warning_ratio: float = 0.75,
    ) -> None:
        self.daily_budget_usd = daily_budget_usd
        self.monthly_budget_usd = monthly_budget_usd
        self.warning_ratio = warning_ratio
        self.daily_spend_usd = 0.0
        self.monthly_spend_usd = 0.0

    def add_spend(self, amount_usd: float) -> None:
        if amount_usd < 0:
            raise ValueError("spend amount must be non-negative")
        self.daily_spend_usd += amount_usd
        self.monthly_spend_usd += amount_usd

    def warnings(self) -> list[str]:
        messages: list[str] = []
        if self.daily_spend_usd >= self.daily_budget_usd * self.warning_ratio:
            messages.append(
                f"Daily spend warning: ${self.daily_spend_usd:.2f} / ${self.daily_budget_usd:.2f}"
            )
        if self.monthly_spend_usd >= self.monthly_budget_usd * self.warning_ratio:
            messages.append(
                f"Monthly spend warning: ${self.monthly_spend_usd:.2f} / ${self.monthly_budget_usd:.2f}"
            )
        return messages

