"""
Example: Data analysis and visualization.

This example demonstrates how to:
1. Fetch historical data
2. Perform data preprocessing
3. Calculate technical indicators
4. Visualize market data
"""

import sys
import os
from datetime import datetime, timedelta

# Add the trading framework to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from trading_framework import XTDataClient
from trading_framework.data import DataProcessor
from trading_framework.utils import setup_logging


def main():
    """Run data analysis example."""
    
    # Setup logging
    setup_logging()
    
    print("=" * 60)
    print("DATA ANALYSIS EXAMPLE")
    print("=" * 60)
    
    try:
        # Initialize data client
        data_client = XTDataClient()
        print("✅ Data client initialized")
        
        # Define symbols and date range
        symbols = ['AAPL', 'GOOGL', 'MSFT']
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        print(f"📅 Date range: {start_date} to {end_date}")
        print(f"📊 Symbols: {', '.join(symbols)}")
        
        # Fetch data for each symbol
        all_data = {}
        
        for symbol in symbols:
            print(f"\n📈 Fetching data for {symbol}...")
            
            # Get historical data
            data = data_client.get_historical_data(
                symbol=symbol,
                interval='1d',
                start_date=start_date,
                end_date=end_date
            )
            
            if not data.empty:
                print(f"✅ Retrieved {len(data)} records for {symbol}")
                
                # Clean and preprocess data
                cleaned_data = DataProcessor.clean_ohlcv_data(data)
                print(f"✅ Cleaned data: {len(cleaned_data)} records remaining")
                
                # Calculate technical indicators
                data_with_indicators = DataProcessor.calculate_technical_indicators(cleaned_data)
                print(f"✅ Calculated technical indicators")
                
                # Calculate returns
                data_with_returns = DataProcessor.calculate_returns(data_with_indicators)
                print(f"✅ Calculated returns")
                
                all_data[symbol] = data_with_returns
                
                # Display basic statistics
                print(f"\n📊 {symbol} Statistics:")
                print(f"   Period: {len(data_with_returns)} days")
                print(f"   Price Range: ${data_with_returns['close'].min():.2f} - ${data_with_returns['close'].max():.2f}")
                print(f"   Average Volume: {data_with_returns['volume'].mean():,.0f}")
                
                if 'return' in data_with_returns.columns:
                    total_return = data_with_returns['return'].add(1).prod() - 1
                    volatility = data_with_returns['return'].std() * (252 ** 0.5)  # Annualized
                    print(f"   Total Return: {total_return:.2%}")
                    print(f"   Volatility: {volatility:.2%}")
                
                # Technical indicators summary
                if 'rsi' in data_with_returns.columns:
                    current_rsi = data_with_returns['rsi'].iloc[-1]
                    print(f"   Current RSI: {current_rsi:.1f}")
                
                if 'sma_20' in data_with_returns.columns:
                    current_price = data_with_returns['close'].iloc[-1]
                    sma_20 = data_with_returns['sma_20'].iloc[-1]
                    price_vs_sma = (current_price / sma_20 - 1) * 100
                    print(f"   Price vs SMA(20): {price_vs_sma:+.1f}%")
            else:
                print(f"❌ No data retrieved for {symbol}")
        
        # Cross-symbol analysis
        if len(all_data) > 1:
            print(f"\n🔍 CROSS-SYMBOL ANALYSIS")
            print("=" * 40)
            
            # Calculate correlations
            import pandas as pd
            
            returns_data = {}
            for symbol, data in all_data.items():
                if 'return' in data.columns:
                    returns_data[symbol] = data['return']
            
            if len(returns_data) > 1:
                returns_df = pd.DataFrame(returns_data).dropna()
                correlations = returns_df.corr()
                
                print("📈 Return Correlations:")
                print(correlations.round(3))
                
                # Find highest and lowest correlations
                corr_values = []
                for i in range(len(correlations.columns)):
                    for j in range(i+1, len(correlations.columns)):
                        symbol1 = correlations.columns[i]
                        symbol2 = correlations.columns[j]
                        corr = correlations.iloc[i, j]
                        corr_values.append((symbol1, symbol2, corr))
                
                if corr_values:
                    corr_values.sort(key=lambda x: x[2], reverse=True)
                    highest = corr_values[0]
                    lowest = corr_values[-1]
                    
                    print(f"\nHighest correlation: {highest[0]} - {highest[1]} ({highest[2]:.3f})")
                    print(f"Lowest correlation: {lowest[0]} - {lowest[1]} ({lowest[2]:.3f})")
        
        # Data quality analysis
        print(f"\n🔍 DATA QUALITY ANALYSIS")
        print("=" * 40)
        
        for symbol, data in all_data.items():
            print(f"\n{symbol}:")
            
            # Check for missing data
            missing_data = data.isnull().sum()
            if missing_data.any():
                print(f"   Missing data points:")
                for col, count in missing_data[missing_data > 0].items():
                    print(f"     {col}: {count}")
            else:
                print(f"   ✅ No missing data")
            
            # Check for outliers in returns
            if 'return' in data.columns:
                returns = data['return'].dropna()
                outliers = DataProcessor.detect_outliers(data, 'return', method='zscore', threshold=3)
                outlier_count = outliers.sum()
                
                if outlier_count > 0:
                    print(f"   ⚠️ Found {outlier_count} return outliers (>3 std dev)")
                    extreme_returns = returns[outliers]
                    if not extreme_returns.empty:
                        print(f"     Extreme returns: {extreme_returns.min():.2%} to {extreme_returns.max():.2%}")
                else:
                    print(f"   ✅ No extreme return outliers")
        
        print(f"\n✅ Data analysis completed successfully!")
        print(f"📝 Analyzed {len(all_data)} symbols with technical indicators")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("ℹ️ Note: Set XTDATA_API_KEY environment variable for live data")
        
        # Show example with mock data
        print(f"\n🔄 Running with mock data example...")
        _run_mock_data_example()
        
    except Exception as e:
        print(f"❌ Error: {e}")


def _run_mock_data_example():
    """Run example with mock data."""
    import pandas as pd
    import numpy as np
    
    print(f"\n📊 MOCK DATA EXAMPLE")
    print("=" * 30)
    
    # Generate mock OHLCV data
    dates = pd.date_range(start='2024-01-01', end='2024-03-31', freq='D')
    np.random.seed(42)  # For reproducible results
    
    # Simulate price movements
    initial_price = 150.0
    returns = np.random.normal(0.001, 0.02, len(dates))  # 0.1% daily return, 2% volatility
    prices = [initial_price]
    
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    mock_data = pd.DataFrame({
        'open': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, len(dates))
    }, index=dates)
    
    # Ensure high >= low and close within range
    mock_data['high'] = np.maximum(mock_data['high'], mock_data[['open', 'close']].max(axis=1))
    mock_data['low'] = np.minimum(mock_data['low'], mock_data[['open', 'close']].min(axis=1))
    
    print(f"✅ Generated {len(mock_data)} days of mock data")
    
    # Apply data processing
    cleaned_data = DataProcessor.clean_ohlcv_data(mock_data)
    print(f"✅ Cleaned data: {len(cleaned_data)} records")
    
    data_with_indicators = DataProcessor.calculate_technical_indicators(cleaned_data)
    print(f"✅ Calculated technical indicators")
    
    data_with_returns = DataProcessor.calculate_returns(data_with_indicators)
    print(f"✅ Calculated returns")
    
    # Display results
    print(f"\n📊 Mock Data Analysis:")
    print(f"   Price Range: ${data_with_returns['close'].min():.2f} - ${data_with_returns['close'].max():.2f}")
    print(f"   Total Return: {(data_with_returns['close'].iloc[-1] / data_with_returns['close'].iloc[0] - 1):.2%}")
    
    if 'rsi' in data_with_returns.columns:
        print(f"   Final RSI: {data_with_returns['rsi'].iloc[-1]:.1f}")
    
    if 'sma_20' in data_with_returns.columns:
        print(f"   Price vs SMA(20): {(data_with_returns['close'].iloc[-1] / data_with_returns['sma_20'].iloc[-1] - 1) * 100:+.1f}%")


if __name__ == "__main__":
    main()