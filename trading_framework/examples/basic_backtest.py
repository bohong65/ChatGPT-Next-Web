"""
Example: Basic backtesting with daily adjustment strategy.

This example demonstrates how to:
1. Set up the trading framework
2. Configure a daily adjustment strategy
3. Run a backtest
4. Analyze results
"""

import sys
import os
from datetime import datetime, timedelta

# Add the trading framework to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from trading_framework import XTDataClient, BacktestEngine
from trading_framework.strategies import DailyAdjustmentStrategy
from trading_framework.config import get_config
from trading_framework.utils import setup_logging


def main():
    """Run basic backtest example."""
    
    # Setup logging
    setup_logging()
    
    print("=" * 60)
    print("BASIC BACKTESTING EXAMPLE")
    print("=" * 60)
    
    # Initialize data client (will use mock data if no API key)
    data_client = None
    try:
        data_client = XTDataClient()
        print("✓ XTData client initialized")
    except ValueError:
        print("⚠ XTData API key not found, using mock data")
    
    # Configure strategy parameters
    strategy_params = {
        'target_weights': {
            'AAPL': 0.3,
            'GOOGL': 0.3,
            'MSFT': 0.2,
            'TSLA': 0.2
        },
        'rebalance_time': '09:30',
        'min_weight_change': 0.05,
        'max_position_size': 0.25
    }
    
    # Initialize strategy
    strategy = DailyAdjustmentStrategy(strategy_params)
    print(f"✓ Strategy initialized: {strategy.name}")
    
    # Initialize backtest engine
    backtest = BacktestEngine(
        strategy=strategy,
        initial_capital=100000,
        commission=0.001,  # 0.1%
        slippage=0.0005,   # 0.05%
        data_client=data_client
    )
    print("✓ Backtest engine initialized")
    
    # Run backtest
    print("\nRunning backtest...")
    
    # Use recent date range
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
    
    try:
        # Run the backtest
        results = backtest.run(
            start_date=start_date,
            end_date=end_date,
            symbols=symbols
        )
        
        print("✓ Backtest completed successfully")
        
        # Display results
        print("\n" + "=" * 60)
        print("BACKTEST RESULTS")
        print("=" * 60)
        
        results.print_summary()
        
        # Additional analysis
        monthly_returns = results.get_monthly_returns()
        if not monthly_returns.empty:
            print(f"\nMonthly Returns Summary:")
            print(f"Best Month: {monthly_returns.max():.2%}")
            print(f"Worst Month: {monthly_returns.min():.2%}")
            print(f"Average Monthly Return: {monthly_returns.mean():.2%}")
        
        # Get strategy-specific information
        strategy_info = strategy.get_strategy_info()
        print(f"\nStrategy Information:")
        print(f"Target Portfolio Value: ${strategy_info['target_portfolio_value']:,.2f}")
        print(f"Last Rebalance: {strategy_info['last_rebalance_date']}")
        
        # Export results to DataFrame for further analysis
        results_df = results.to_dataframe()
        if not results_df.empty:
            print(f"\nPortfolio value history: {len(results_df)} data points")
            print("Use results.to_dataframe() for detailed analysis")
        
    except Exception as e:
        print(f"✗ Backtest failed: {e}")
        
        # Show backtest summary even if failed
        summary = backtest.get_backtest_summary()
        print(f"\nBacktest Summary:")
        for key, value in summary.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()