"""TapeLab: transparent backtests for bar-based strategy research."""

from tapelab.engine import run_backtest
from tapelab.models import BacktestConfig, BacktestResult, Bar, EquityPoint, Fill

__all__ = [
    "BacktestConfig",
    "BacktestResult",
    "Bar",
    "EquityPoint",
    "Fill",
    "run_backtest",
]

__version__ = "0.1.0"

