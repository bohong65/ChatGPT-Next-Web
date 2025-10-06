# Quantitative Trading Strategy Framework

A modular Python framework for quantitative trading that integrates with XTData for historical and real-time data and XTTrader for order execution.

## Features

- **Data Module**: Connect to XTData API for historical and real-time market data
- **Strategy Module**: Implement custom trading strategies with daily adjustment and 5-minute interval logic
- **Backtest Module**: Simulate historical trades and calculate performance metrics
- **Execution Module**: Connect to XTTrader API for live trading
- **Configuration**: Flexible configuration management with environment variable support
- **Logging**: Comprehensive logging for execution tracking and debugging

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your API keys in `config/config.yaml` or set environment variables:
```bash
export XTDATA_API_KEY="your_xtdata_api_key"
export XTTRADER_API_KEY="your_xttrader_api_key"
```

3. Run a backtest:
```python
from trading_framework.backtest import BacktestEngine
from trading_framework.strategies.daily_strategy import DailyAdjustmentStrategy

strategy = DailyAdjustmentStrategy()
backtest = BacktestEngine(strategy)
results = backtest.run('2023-01-01', '2023-12-31')
print(f"Total Return: {results.total_return:.2%}")
```

## Module Structure

- `data/`: Data retrieval and preprocessing
- `strategies/`: Trading strategy implementations
- `backtest/`: Backtesting engine and performance metrics
- `execution/`: Live trading execution
- `config/`: Configuration management
- `utils/`: Utility functions and logging

## Documentation

See individual module documentation in each directory for detailed usage instructions.