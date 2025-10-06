"""
Backtest Module for simulating trading strategies on historical data.

Provides backtesting engine and performance metrics calculation.
"""

from .backtest_engine import BacktestEngine
from .performance_metrics import PerformanceMetrics

__all__ = ["BacktestEngine", "PerformanceMetrics"]