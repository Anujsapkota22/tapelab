"""Strategy interface and a small moving-average example."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from tapelab.models import Bar


class Strategy(Protocol):
    """Return the desired long-only portfolio weight for the current bar.

    The engine passes history ending at the current bar. A returned target is
    actionable only after this bar closes and is filled at the next bar's open.
    Return a number from 0 (cash) to 1 (fully invested).
    """

    def target_weight(self, bar: Bar, history: Sequence[Bar]) -> float:
        """Choose a target allocation using only bars available so far."""


@dataclass(frozen=True, slots=True)
class MovingAverageCrossover:
    """Long when a short simple moving average is above a long one."""

    fast: int = 5
    slow: int = 20

    def __post_init__(self) -> None:
        if self.fast <= 0 or self.slow <= 0:
            raise ValueError("moving-average windows must be positive")
        if self.fast >= self.slow:
            raise ValueError("fast window must be smaller than slow window")

    def target_weight(self, bar: Bar, history: Sequence[Bar]) -> float:
        if len(history) < self.slow:
            return 0.0
        fast_mean = sum(item.close for item in history[-self.fast :]) / self.fast
        slow_mean = sum(item.close for item in history[-self.slow :]) / self.slow
        return 1.0 if fast_mean > slow_mean else 0.0

