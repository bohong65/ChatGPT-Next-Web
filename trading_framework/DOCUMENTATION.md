# Trading Framework Documentation

## Overview

The Quantitative Trading Strategy Framework is a modular Python framework designed for algorithmic trading with XTData and XTTrader API integration. It provides a comprehensive solution for data acquisition, strategy development, backtesting, and live trading execution.

## Architecture

The framework is organized into six main modules:

### 1. Data Module (`data/`)
Handles market data acquisition and preprocessing.

**Key Components:**
- `XTDataClient`: Connects to XTData API for historical and real-time market data
- `DataProcessor`: Provides data cleaning, technical indicators, and preprocessing utilities

**Features:**
- Historical OHLCV data fetching
- Real-time WebSocket data streaming
- Data validation and cleaning
- Technical indicator calculations (RSI, MACD, Bollinger Bands, etc.)
- Data normalization and outlier detection

### 2. Strategy Module (`strategies/`)
Contains trading strategy implementations and base classes.

**Key Components:**
- `BaseStrategy`: Abstract base class for all trading strategies
- `DailyAdjustmentStrategy`: Daily portfolio rebalancing strategy
- `MinuteIntervalStrategy`: High-frequency 5-minute interval strategy

**Features:**
- Signal generation framework
- Position management
- Risk controls
- Strategy performance tracking

### 3. Backtest Module (`backtest/`)
Provides backtesting capabilities for strategy validation.

**Key Components:**
- `BacktestEngine`: Main backtesting engine
- `PerformanceMetrics`: Comprehensive performance analysis

**Features:**
- Historical simulation
- Transaction cost modeling (commission, slippage)
- Performance metrics (Sharpe ratio, max drawdown, etc.)
- Trade analysis and reporting

### 4. Execution Module (`execution/`)
Handles live trading execution via XTTrader API.

**Key Components:**
- `XTTraderClient`: Connects to XTTrader API for order execution
- `Order`: Order management and tracking

**Features:**
- Market and limit orders
- Order status monitoring
- Position management
- Account information retrieval

### 5. Configuration Module (`config/`)
Manages framework configuration and settings.

**Key Components:**
- `config_manager`: Configuration loading and management
- `config.yaml`: Default configuration file

**Features:**
- YAML configuration files
- Environment variable support
- Secure API key management
- Default settings and validation

### 6. Utils Module (`utils/`)
Provides utility functions and logging setup.

**Key Components:**
- `logger`: Logging configuration
- `helpers`: Common utility functions

**Features:**
- Structured logging with file rotation
- Position sizing calculations
- Currency formatting
- Market hours validation

## Installation

1. **Clone or download the framework:**
```bash
git clone <repository_url>
cd trading_framework
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure API keys:**
```bash
# Copy environment template
cp .env.template .env

# Edit .env with your API keys
export XTDATA_API_KEY="your_xtdata_api_key"
export XTTRADER_API_KEY="your_xttrader_api_key"
export XTTRADER_SECRET_KEY="your_xttrader_secret_key"
```

## Quick Start

### Basic Backtesting

```python
from trading_framework import BacktestEngine
from trading_framework.strategies import DailyAdjustmentStrategy

# Configure strategy
strategy = DailyAdjustmentStrategy({
    'target_weights': {'AAPL': 0.5, 'GOOGL': 0.5},
    'rebalance_time': '09:30'
})

# Run backtest
backtest = BacktestEngine(strategy, initial_capital=100000)
results = backtest.run('2023-01-01', '2023-12-31', ['AAPL', 'GOOGL'])

# View results
results.print_summary()
```

### Live Trading Setup

```python
from trading_framework import XTDataClient, XTTraderClient
from trading_framework.strategies import MinuteIntervalStrategy

# Initialize clients
data_client = XTDataClient()
trader_client = XTTraderClient()

# Configure strategy
strategy = MinuteIntervalStrategy({
    'rsi_oversold': 30,
    'rsi_overbought': 70,
    'stop_loss_pct': 0.02
})

# Implement your trading loop
# (See examples/live_trading.py for complete implementation)
```

### Data Analysis

```python
from trading_framework.data import XTDataClient, DataProcessor

# Fetch data
client = XTDataClient()
data = client.get_historical_data('AAPL', '1d', '2023-01-01', '2023-12-31')

# Process data
clean_data = DataProcessor.clean_ohlcv_data(data)
data_with_indicators = DataProcessor.calculate_technical_indicators(clean_data)

# Analyze
print(f"RSI: {data_with_indicators['rsi'].iloc[-1]:.1f}")
```

## Configuration

The framework uses YAML configuration files and environment variables. Key configuration sections:

### XTData Settings
```yaml
xtdata:
  base_url: "https://api.xtdata.com"
  api_key: null  # Set via XTDATA_API_KEY env var
  timeout: 30
```

### XTTrader Settings
```yaml
xttrader:
  base_url: "https://api.xttrader.com"
  api_key: null      # Set via XTTRADER_API_KEY env var
  secret_key: null   # Set via XTTRADER_SECRET_KEY env var
```

### Risk Management
```yaml
risk_management:
  max_position_size: 0.1      # 10% max per position
  max_daily_loss: 0.02        # 2% daily loss limit
  stop_loss_default: 0.02     # 2% default stop loss
```

## Strategy Development

### Creating Custom Strategies

1. **Inherit from BaseStrategy:**
```python
from trading_framework.strategies import BaseStrategy, Signal

class MyStrategy(BaseStrategy):
    def initialize(self, data):
        # Strategy initialization
        pass
    
    def generate_signals(self, data, timestamp):
        # Generate trading signals
        signals = []
        
        # Your logic here
        if condition:
            signal = Signal('AAPL', 'BUY', 100)
            signals.append(signal)
        
        return signals
```

2. **Implement required methods:**
- `initialize()`: One-time setup with historical data
- `generate_signals()`: Generate trading signals based on current data

3. **Use Signal objects for trading decisions:**
```python
signal = Signal(
    symbol='AAPL',
    action='BUY',  # or 'SELL', 'HOLD'
    quantity=100,
    price=150.0,   # Optional: None for market orders
    confidence=0.8 # Signal confidence (0-1)
)
```

## Performance Metrics

The framework calculates comprehensive performance metrics:

### Return Metrics
- Total Return
- Annualized Return
- Monthly/Yearly Returns

### Risk Metrics
- Volatility (annualized)
- Maximum Drawdown
- Sharpe Ratio
- Sortino Ratio

### Trade Statistics
- Total Trades
- Win Rate
- Profit Factor
- Average Win/Loss
- Trade Duration

### Usage Example
```python
# After running backtest
results = backtest.run(start_date, end_date, symbols)

print(f"Total Return: {results.total_return:.2%}")
print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
print(f"Max Drawdown: {results.max_drawdown:.2%}")

# Get detailed metrics
summary = results.get_summary()
```

## Risk Management

### Position Sizing
The framework includes automatic position sizing based on risk parameters:

```python
from trading_framework.utils import calculate_position_size

position_size = calculate_position_size(
    account_value=100000,
    risk_per_trade=0.02,      # 2% risk
    entry_price=150.0,
    stop_loss_price=147.0
)
```

### Risk Controls
- Maximum position size limits
- Daily loss limits
- Stop loss and take profit automation
- Drawdown monitoring

## Logging

The framework uses structured logging with file rotation:

```python
from trading_framework.utils import setup_logging, get_logger

# Setup logging
setup_logging()

# Get logger for your module
logger = get_logger(__name__)

logger.info("Trading started")
logger.error("Order failed", extra={'symbol': 'AAPL'})
```

## Examples

The `examples/` directory contains complete working examples:

- `basic_backtest.py`: Simple backtesting example
- `live_trading.py`: Real-time trading implementation
- `data_analysis.py`: Data analysis and visualization

Run examples:
```bash
cd examples
python basic_backtest.py
python data_analysis.py
```

## Testing

Run the framework tests:
```bash
python -m pytest tests/
```

## Security Considerations

1. **API Key Management:**
   - Never commit API keys to version control
   - Use environment variables or secure key management
   - Regularly rotate API keys

2. **Live Trading:**
   - Start with paper trading
   - Implement position limits
   - Monitor for unusual behavior
   - Have emergency stop procedures

3. **Data Validation:**
   - Validate all market data
   - Implement sanity checks
   - Handle API failures gracefully

## Troubleshooting

### Common Issues

1. **API Connection Errors:**
   - Check API keys are set correctly
   - Verify network connectivity
   - Check API rate limits

2. **Data Issues:**
   - Validate symbol formats
   - Check date ranges
   - Handle missing data gracefully

3. **Strategy Errors:**
   - Implement proper error handling
   - Validate signals before execution
   - Monitor position limits

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python your_script.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This framework is provided as-is for educational and research purposes. Use in live trading at your own risk.

## Support

For issues and questions:
1. Check the documentation
2. Review example implementations
3. Check error logs
4. Create an issue in the repository

## Disclaimer

⚠️ **Trading Risk Warning**: Trading in financial markets involves substantial risk of loss. Past performance is not indicative of future results. This framework is for educational purposes only. Always test strategies thoroughly before risking real capital.