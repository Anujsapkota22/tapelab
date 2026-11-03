# TapeLab

**A small, auditable Python engine for bar-based strategy research.** TapeLab makes signal timing, next-bar execution, transaction costs, and portfolio accounting explicit so a backtest is easier to inspect and reproduce.

> TapeLab is an early-stage research tool. It is not a broker, does not place orders, and does not provide investment advice. The included price data is synthetic and demonstrates software behavior only.

## Why this project

Backtest results are easy to misread when a strategy can trade at the same close used to create its signal, or when fees and slippage disappear from the ledger. TapeLab keeps the core engine small enough to read and sets conservative, visible defaults: signals use only data through the current close, orders wait until the next bar's open, and fills include configurable costs.

This makes the project useful for learning, prototyping, and reviewing assumptions before a researcher chooses a larger data or execution stack. See [the design notes](docs/design.md) for the accounting rules and current limits.

## Install

Requires Python 3.11 or newer. The engine has no runtime dependencies.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\Activate.ps1
python -m pip install -e .
```

## Run the included example

```bash
tapelab \
  --data examples/data/sample_ohlcv.csv \
  --strategy sma-crossover \
  --fast 4 --slow 9 \
  --cash 10000 \
  --fee-bps 1 --slippage-bps 2 \
  --output out/sample-report.json
```

The command prints a compact metric summary and writes a JSON report containing settings, fills, and the marked-to-market equity curve. The sample CSV is a small, synthetic series—not market history. You can also run `python examples/run_backtest.py` from the repository root.

## Execution model

```text
bar N closes -> strategy chooses a target -> bar N+1 opens -> order fills -> bar N+1 closes -> equity is marked
```

- Strategies receive immutable OHLCV bars from the start through the current bar. They cannot see future rows through the engine API.
- A changed target allocation creates one order, filled at the next bar's open. A target does not continuously rebalance just because its market value drifts.
- Buys pay adverse upward slippage; sells pay adverse downward slippage. Fees and slippage are configured in basis points and recorded on every fill.
- The engine is long-only, uses one asset, permits fractional quantities, and begins in cash. An order generated on the final bar has no later open at which to fill.
- Open positions are marked to the final close; the engine does not force a final liquidation or charge a hypothetical closing fee.

## Use the Python API

```python
from tapelab import BacktestConfig, run_backtest
from tapelab.data import load_bars
from tapelab.metrics import summarize
from tapelab.strategy import MovingAverageCrossover

bars = load_bars("examples/data/sample_ohlcv.csv")
strategy = MovingAverageCrossover(fast=4, slow=9)
settings = BacktestConfig(initial_cash=10_000, fee_bps=1, slippage_bps=2)

result = run_backtest(bars, strategy, settings)
print(summarize(result, settings.periods_per_year))
```

To add a strategy, implement `target_weight(bar, history)` and return a finite allocation from `0.0` (cash) to `1.0` (fully invested). The history includes the current bar. The engine validates the returned allocation.

## Input data

CSV files must include `timestamp,open,high,low,close,volume` columns. Timestamps use ISO 8601; naive timestamps are interpreted as UTC. Rows must be strictly increasing and unique. Extra columns are ignored. Invalid prices, inconsistent OHLC ranges, non-finite values, and negative volume are rejected with a row-specific error.

## Metrics and assumptions

Reports include total return, CAGR, annualized volatility, a zero-risk-free Sharpe ratio, maximum marked-to-market drawdown, invested-bar exposure, fill count, and sell-fill count. Set `periods_per_year` to match the bar frequency (252 for daily bars is a convention, not a universal constant). A short sample can make annualized metrics unstable or meaningless; inspect the full curve and assumptions.

## Scope and roadmap

Current scope is intentionally narrow: one asset, OHLCV bars, long-only target allocations, next-open fills, fees, and fixed slippage. TapeLab does not model short sales, margin, borrow costs, dividends, splits, partial fills, order books, market impact, limit/stop orders, intrabar sequencing, exchange calendars, or survivorship-free datasets.

Planned work is tracked in [the roadmap](docs/roadmap.md): stronger accounting invariants, broader execution models, portfolio support, and reproducible benchmark datasets. Contributions and carefully scoped issues are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md).

## Project status

TapeLab is a new public project at version 0.1.0. It has no adoption or download claims. The first milestone is a readable, reproducible baseline that can be reviewed and improved in the open.

## License

MIT. See [LICENSE](LICENSE).

