# Design and accounting rules

TapeLab aims to make the path from a strategy decision to portfolio value explicit. The engine is small on purpose: users should be able to inspect timing and cash movements without first learning a framework's hidden conventions.

## Event sequence

For each bar, in timestamp order, TapeLab:

1. Fills any target produced after the prior bar's close at this bar's open.
2. Marks cash plus the open position at this bar's close and records an equity point.
3. Calls the strategy with this bar and an immutable history ending at this bar.
4. Schedules an order only if the requested target differs from the last requested target.

A last-bar signal remains pending and is not filled. A position is not automatically closed at the end of the data.

## Fill and cash model

The strategy chooses a long-only target allocation between zero and one. At an execution open, the target quantity is based on portfolio equity marked at the open. A buy fill price is open multiplied by `1 + slippage_bps / 10,000`; a sell uses open multiplied by `1 - slippage_bps / 10,000`. Fees are charged on the absolute traded notional. Buy quantity is capped so the cash balance, including its fee, cannot go below zero. Fractional quantities are allowed.

This simple model captures directionally adverse costs but does not claim to reproduce a particular broker, venue, or order book. It has no market impact or partial-fill model.

## Mark-to-market and metrics

Each equity point is `cash + quantity * close`. Drawdown uses these points, so an open position contributes to drawdown. Returns are adjacent equity-point returns; annualized metrics use the configured number of periods per year. Sharpe assumes a zero risk-free rate. CAGR uses the initial cash and the number of observed intervals.

The engine reports fill counts rather than inferring completed round trips. A sell-fill count can include a reduction in allocation, not only a full exit.

## Data boundary

All timestamps are normalized to UTC by the CSV loader; naive timestamp strings are interpreted as UTC. The engine checks strict timestamp ordering again, so callers that construct `Bar` instances directly receive the same ordering protection. It validates finite, positive prices and basic OHLC consistency. It cannot detect bad vendor adjustments, missing bars, or survivorship bias in a dataset.

## Non-goals for the first release

- Live or paper trading, brokerage integration, or trade recommendations.
- Shorting, leverage, multi-asset portfolio accounting, or corporate-action processing.
- Tick-level execution, stop/limit simulation, or intrabar ordering assumptions.
- A claim that a high historical return predicts future performance.

