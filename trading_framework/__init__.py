"""
Quantitative Trading Strategy Framework

A modular Python framework for algorithmic trading with XTData and XTTrader integration.
"""

__version__ = "1.0.0"
__author__ = "Trading Framework Team"

# Import main classes - handle import errors gracefully for documentation generation
try:
    from .data import XTDataClient
    from .strategies import BaseStrategy
    from .backtest import BacktestEngine
    from .execution import XTTraderClient
    
    __all__ = [
        "XTDataClient",
        "BaseStrategy", 
        "BacktestEngine",
        "XTTraderClient"
    ]
except ImportError:
    # Allow module to be imported even if dependencies are missing
    __all__ = []