"""Deterministic next-bar-open execution for long-only target allocations."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

from tapelab.models import BacktestConfig, BacktestResult, Bar, EquityPoint, Fill
from tapelab.strategy import Strategy


class _HistoryView(Sequence[Bar]):
    """Read-only prefix of the input bars, without copying the whole prefix."""

    __slots__ = ("_bars", "_length")

    def __init__(self, bars: tuple[Bar, ...], length: int) -> None:
        object.__setattr__(self, "_bars", bars)
        object.__setattr__(self, "_length", length)

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("history views are immutable")

    def __len__(self) -> int:
        return self._length

    def __getitem__(self, index: int | slice) -> Bar | tuple[Bar, ...]:
        if isinstance(index, slice):
            start, stop, step = index.indices(self._length)
            return tuple(self._bars[position] for position in range(start, stop, step))
        if index < 0:
            index += self._length
        if not 0 <= index < self._length:
            raise IndexError("history index out of range")
        return self._bars[index]


def _execute_target(
    *,
    timestamp,
    open_price: float,
    target_weight: float,
    cash: float,
    quantity: float,
    config: BacktestConfig,
) -> tuple[float, float, Fill | None]:
    """Rebalance once at the open, including adverse slippage and fees."""

    fee_rate = config.fee_bps / 10_000.0
    slippage_rate = config.slippage_bps / 10_000.0
    reference_equity = cash + quantity * open_price
    if reference_equity <= 0:
        return cash, quantity, None

    # The target's notional is based on open-marked equity; execution uses the
    # adverse fill price so slippage is reflected in both cash and holdings.
    buy_reference_price = open_price * (1.0 + slippage_rate)
    sell_reference_price = open_price * (1.0 - slippage_rate)
    target_quantity = reference_equity * target_weight / open_price

    if target_quantity > quantity:
        delta = target_quantity - quantity
        fill_price = buy_reference_price
        # Include fees in the affordability check so cash cannot go negative.
        affordable = cash / (fill_price * (1.0 + fee_rate)) if cash > 0 else 0.0
        delta = min(delta, affordable)
        if delta <= 1e-12:
            return cash, quantity, None
        fee = delta * fill_price * fee_rate
        cash -= delta * fill_price + fee
        quantity += delta
        return cash, quantity, Fill(timestamp, "buy", delta, fill_price, fee, target_weight)

    if target_quantity < quantity:
        delta = quantity - target_quantity
        fill_price = sell_reference_price
        fee = delta * fill_price * fee_rate
        cash += delta * fill_price - fee
        quantity -= delta
        return cash, quantity, Fill(timestamp, "sell", delta, fill_price, fee, target_weight)

    return cash, quantity, None


def run_backtest(
    bars: Iterable[Bar],
    strategy: Strategy,
    config: BacktestConfig | None = None,
) -> BacktestResult:
    """Run a strategy over ascending OHLCV bars.

    Signals are evaluated after each close, then filled at the next bar's open.
    A signal generated on the last bar remains unfilled. The engine is
    long-only, holds one asset, and does not force liquidation at the end.
    """

    settings = config or BacktestConfig()
    data = tuple(bars)
    equity_curve: list[EquityPoint] = []
    fills: list[Fill] = []
    cash = settings.initial_cash
    quantity = 0.0
    pending_target: float | None = None
    last_requested_target = 0.0
    previous_timestamp = None

    for index, bar in enumerate(data):
        if previous_timestamp is not None and bar.timestamp <= previous_timestamp:
            raise ValueError("bars must have strictly increasing, unique timestamps")
        previous_timestamp = bar.timestamp

        if pending_target is not None:
            cash, quantity, fill = _execute_target(
                timestamp=bar.timestamp,
                open_price=bar.open,
                target_weight=pending_target,
                cash=cash,
                quantity=quantity,
                config=settings,
            )
            if fill is not None:
                fills.append(fill)
            pending_target = None

        equity = cash + quantity * bar.close
        equity_curve.append(EquityPoint(bar.timestamp, cash, quantity, bar.close, equity))
        history = _HistoryView(data, index + 1)
        target = float(strategy.target_weight(bar, history))
        if not math.isfinite(target) or not 0.0 <= target <= 1.0:
            raise ValueError("strategy target_weight must be a finite value from 0 to 1")

        # Only create an order when intent changes. The engine does not
        # continuously rebalance a position just because its market weight drifted.
        if not math.isclose(target, last_requested_target, abs_tol=1e-12):
            pending_target = target
            last_requested_target = target

    if not equity_curve:
        raise ValueError("at least one bar is required")

    return BacktestResult(
        initial_cash=settings.initial_cash,
        equity_curve=tuple(equity_curve),
        fills=tuple(fills),
        final_cash=cash,
        final_position_quantity=quantity,
    )

