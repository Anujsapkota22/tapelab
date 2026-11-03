"""Run the included synthetic-data example from the repository root."""

from pathlib import Path

from tapelab.data import load_bars
from tapelab.engine import run_backtest
from tapelab.metrics import summarize
from tapelab.models import BacktestConfig
from tapelab.report import result_payload, write_json
from tapelab.strategy import MovingAverageCrossover

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "examples" / "data" / "sample_ohlcv.csv"

config = BacktestConfig(initial_cash=10_000, fee_bps=1, slippage_bps=2)
strategy = MovingAverageCrossover(fast=4, slow=9)
result = run_backtest(load_bars(DATA), strategy, config)
report = write_json(
    result_payload(result, config, "sma-crossover"),
    ROOT / "examples" / "sample_report.json",
)

print(f"Report: {report.relative_to(ROOT)}")
print(summarize(result, config.periods_per_year))

