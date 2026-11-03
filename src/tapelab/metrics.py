"""Small, dependency-free summary metrics for a backtest result."""

from __future__ import annotations

import math

from tapelab.models import BacktestResult


def summarize(result: BacktestResult, periods_per_year: int = 252) -> dict[str, float | int | None]:
    """Calculate return, risk, drawdown, exposure, and execution summaries."""

    if not result.equity_curve:
        raise ValueError("cannot summarize a result with no equity observations")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be greater than zero")

    equities = [point.equity for point in result.equity_curve]
    final_equity = equities[-1]
    total_return = final_equity / result.initial_cash - 1.0
    bar_intervals = max(len(equities) - 1, 0)
    if final_equity <= 0:
        cagr: float | None = None
    elif bar_intervals == 0:
        cagr = total_return
    else:
        cagr = (final_equity / result.initial_cash) ** (periods_per_year / bar_intervals) - 1.0

    returns = [current / previous - 1.0 for previous, current in zip(equities, equities[1:])]
    volatility: float | None = None
    sharpe: float | None = None
    if len(returns) > 1:
        mean_return = sum(returns) / len(returns)
        variance = sum((value - mean_return) ** 2 for value in returns) / (len(returns) - 1)
        volatility = math.sqrt(variance * periods_per_year)
        if volatility > 0:
            sharpe = mean_return * periods_per_year / volatility
        else:
            sharpe = 0.0
    elif len(returns) == 1:
        volatility = 0.0
        sharpe = 0.0

    peak = equities[0]
    max_drawdown = 0.0
    for equity in equities:
        peak = max(peak, equity)
        if peak > 0:
            max_drawdown = min(max_drawdown, equity / peak - 1.0)

    invested_bars = sum(
        1 for point in result.equity_curve if point.position_quantity * point.close > 0
    )
    exposure = invested_bars / len(result.equity_curve)

    return {
        "initial_cash": result.initial_cash,
        "final_equity": final_equity,
        "total_return": total_return,
        "cagr": cagr,
        "annualized_volatility": volatility,
        "sharpe_ratio": sharpe,
        "max_drawdown": max_drawdown,
        "exposure": exposure,
        "fill_count": len(result.fills),
        "closed_position_fills": sum(1 for fill in result.fills if fill.side == "sell"),
    }

