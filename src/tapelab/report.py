"""Stable JSON serialization for backtest outputs."""

from __future__ import annotations

import json
from datetime import timezone
from pathlib import Path
from typing import Any

from tapelab.metrics import summarize
from tapelab.models import BacktestConfig, BacktestResult


def _timestamp(value) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def result_payload(
    result: BacktestResult,
    config: BacktestConfig,
    strategy_name: str,
) -> dict[str, Any]:
    """Build a JSON-friendly report payload without hiding simulation settings."""

    return {
        "project": "TapeLab",
        "schema_version": 1,
        "strategy": strategy_name,
        "settings": {
            "initial_cash": config.initial_cash,
            "fee_bps": config.fee_bps,
            "slippage_bps": config.slippage_bps,
            "periods_per_year": config.periods_per_year,
        },
        "metrics": summarize(result, config.periods_per_year),
        "final_cash": result.final_cash,
        "final_position_quantity": result.final_position_quantity,
        "fills": [
            {
                "timestamp": _timestamp(fill.timestamp),
                "side": fill.side,
                "quantity": fill.quantity,
                "price": fill.price,
                "fee": fill.fee,
                "target_weight": fill.target_weight,
            }
            for fill in result.fills
        ],
        "equity_curve": [
            {
                "timestamp": _timestamp(point.timestamp),
                "cash": point.cash,
                "position_quantity": point.position_quantity,
                "close": point.close,
                "equity": point.equity,
            }
            for point in result.equity_curve
        ],
    }


def write_json(payload: dict[str, Any], destination: str | Path) -> Path:
    """Write a deterministic, human-readable JSON report."""

    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return path

