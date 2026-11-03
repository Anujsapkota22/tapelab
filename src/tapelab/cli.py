"""Command-line entry point for running and exporting a backtest."""

from __future__ import annotations

import argparse
import json
import sys

from tapelab.data import load_bars
from tapelab.engine import run_backtest
from tapelab.metrics import summarize
from tapelab.models import BacktestConfig
from tapelab.report import result_payload, write_json
from tapelab.strategy import MovingAverageCrossover


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tapelab",
        description="Run an auditable, next-bar-open backtest over OHLCV CSV data.",
    )
    parser.add_argument("--data", required=True, help="CSV with timestamp, open, high, low, close, volume")
    parser.add_argument("--strategy", choices=("sma-crossover",), default="sma-crossover")
    parser.add_argument("--fast", type=int, default=5, help="fast SMA window in bars")
    parser.add_argument("--slow", type=int, default=20, help="slow SMA window in bars")
    parser.add_argument("--cash", type=float, default=10_000.0, help="initial cash")
    parser.add_argument("--fee-bps", type=float, default=1.0, help="commission per fill in basis points")
    parser.add_argument("--slippage-bps", type=float, default=2.0, help="adverse slippage per fill in basis points")
    parser.add_argument(
        "--periods-per-year",
        type=int,
        default=252,
        help="annualization periods used for risk metrics (252 for daily bars)",
    )
    parser.add_argument("--output", help="optional path for a full JSON report")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        config = BacktestConfig(
            initial_cash=args.cash,
            fee_bps=args.fee_bps,
            slippage_bps=args.slippage_bps,
            periods_per_year=args.periods_per_year,
        )
        strategy = MovingAverageCrossover(fast=args.fast, slow=args.slow)
        bars = load_bars(args.data)
        result = run_backtest(bars, strategy, config)
        payload = result_payload(result, config, args.strategy)
        if args.output:
            report_path = write_json(payload, args.output)
            print(f"Wrote report: {report_path}")
        print(json.dumps(summarize(result, config.periods_per_year), indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError) as exc:
        print(f"tapelab: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

