"""Core immutable data structures used by the engine."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True, slots=True)
class Bar:
    """One OHLCV bar. Timestamps must be timezone-aware."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("bar timestamp must include a timezone")
        values = (self.open, self.high, self.low, self.close, self.volume)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("OHLCV values must be finite numbers")
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("OHLC prices must be greater than zero")
        if self.volume < 0:
            raise ValueError("volume cannot be negative")
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high must be at least as large as open, close, and low")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low must be no larger than open, close, and high")


@dataclass(frozen=True, slots=True)
class BacktestConfig:
    """Simulation settings. Costs are expressed in basis points."""

    initial_cash: float = 10_000.0
    fee_bps: float = 1.0
    slippage_bps: float = 2.0
    periods_per_year: int = 252

    def __post_init__(self) -> None:
        if not math.isfinite(self.initial_cash) or self.initial_cash <= 0:
            raise ValueError("initial_cash must be a finite number greater than zero")
        if not math.isfinite(self.fee_bps) or self.fee_bps < 0:
            raise ValueError("fee_bps must be a finite non-negative number")
        if not math.isfinite(self.slippage_bps) or not 0 <= self.slippage_bps < 10_000:
            raise ValueError("slippage_bps must be in the range [0, 10000)")
        if self.periods_per_year <= 0:
            raise ValueError("periods_per_year must be greater than zero")


@dataclass(frozen=True, slots=True)
class Fill:
    """A simulated market fill at the next bar's open."""

    timestamp: datetime
    side: Literal["buy", "sell"]
    quantity: float
    price: float
    fee: float
    target_weight: float


@dataclass(frozen=True, slots=True)
class EquityPoint:
    """Portfolio value marked to the bar close."""

    timestamp: datetime
    cash: float
    position_quantity: float
    close: float
    equity: float


@dataclass(frozen=True, slots=True)
class BacktestResult:
    """Immutable output from one simulation run."""

    initial_cash: float
    equity_curve: tuple[EquityPoint, ...]
    fills: tuple[Fill, ...]
    final_cash: float
    final_position_quantity: float

