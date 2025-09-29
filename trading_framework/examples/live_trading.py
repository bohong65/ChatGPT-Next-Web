"""
Example: Real-time trading with 5-minute strategy.

This example demonstrates how to:
1. Set up real-time data streaming
2. Configure a 5-minute interval strategy
3. Execute live trades
4. Monitor performance

⚠️ WARNING: This example executes real trades!
Make sure you understand the risks before running.
"""

import sys
import os
import time
from datetime import datetime

# Add the trading framework to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from trading_framework import XTDataClient, XTTraderClient
from trading_framework.strategies import MinuteIntervalStrategy
from trading_framework.config import get_config
from trading_framework.utils import setup_logging


class LiveTradingEngine:
    """Simple live trading engine for demonstration."""
    
    def __init__(self, strategy, data_client, trader_client):
        self.strategy = strategy
        self.data_client = data_client
        self.trader_client = trader_client
        self.running = False
        self.symbols = ['AAPL', 'GOOGL']  # Trading symbols
    
    def start(self):
        """Start live trading."""
        print("🚀 Starting live trading engine...")
        self.running = True
        
        # Subscribe to real-time data
        self.data_client.subscribe_real_time(
            symbols=self.symbols,
            callback=self._on_market_data
        )
        
        print(f"📊 Subscribed to real-time data for: {', '.join(self.symbols)}")
        
        # Main trading loop
        try:
            while self.running:
                # Check account status
                account_info = self.trader_client.get_account_info()
                if account_info:
                    print(f"💰 Account Balance: ${account_info.get('balance', 0):,.2f}")
                
                # Update order status
                self.trader_client.update_all_orders()
                
                # Display active orders
                active_orders = self.trader_client.get_active_orders()
                if active_orders:
                    print(f"📋 Active Orders: {len(active_orders)}")
                
                # Sleep for 30 seconds
                time.sleep(30)
                
        except KeyboardInterrupt:
            print("\n⏹️ Stopping live trading...")
            self.stop()
    
    def stop(self):
        """Stop live trading."""
        self.running = False
        
        # Unsubscribe from data
        self.data_client.unsubscribe_real_time()
        
        # Cancel all pending orders (optional)
        print("❌ Cancelling all pending orders...")
        self.trader_client.cancel_all_orders()
        
        print("✅ Live trading stopped")
    
    def _on_market_data(self, data):
        """Handle incoming market data."""
        try:
            if 'symbol' in data and 'price' in data:
                symbol = data['symbol']
                price = float(data['price'])
                timestamp = datetime.now()
                
                print(f"📈 {symbol}: ${price:.2f}")
                
                # Create a simple DataFrame for the strategy
                # In a real implementation, you'd maintain a proper data buffer
                import pandas as pd
                
                # Simulate recent data (in practice, you'd maintain a rolling window)
                market_data = pd.DataFrame({
                    'close': [price],
                    'volume': [data.get('volume', 1000000)]
                }, index=[timestamp])
                
                # Generate signals
                signals = self.strategy.on_data(market_data, timestamp)
                
                # Execute signals
                for signal in signals:
                    self._execute_signal(signal)
                    
        except Exception as e:
            print(f"❌ Error processing market data: {e}")
    
    def _execute_signal(self, signal):
        """Execute a trading signal."""
        print(f"🎯 Signal: {signal}")
        
        try:
            if signal.action == 'BUY':
                order = self.trader_client.buy(
                    symbol=signal.symbol,
                    quantity=signal.quantity,
                    price=signal.price
                )
                if order:
                    print(f"✅ Buy order placed: {order}")
                else:
                    print(f"❌ Failed to place buy order")
                    
            elif signal.action == 'SELL':
                order = self.trader_client.sell(
                    symbol=signal.symbol,
                    quantity=signal.quantity,
                    price=signal.price
                )
                if order:
                    print(f"✅ Sell order placed: {order}")
                else:
                    print(f"❌ Failed to place sell order")
                    
        except Exception as e:
            print(f"❌ Error executing signal: {e}")


def main():
    """Run live trading example."""
    
    # Setup logging
    setup_logging()
    
    print("=" * 60)
    print("LIVE TRADING EXAMPLE")
    print("⚠️  WARNING: This will execute real trades!")
    print("=" * 60)
    
    # Confirm user wants to proceed
    response = input("Do you want to proceed with live trading? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Live trading cancelled")
        return
    
    try:
        # Initialize clients
        data_client = XTDataClient()
        trader_client = XTTraderClient()
        
        print("✅ Clients initialized successfully")
        
        # Configure strategy
        strategy_params = {
            'interval_minutes': 5,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'max_positions': 5,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.04
        }
        
        strategy = MinuteIntervalStrategy(strategy_params)
        print(f"✅ Strategy configured: {strategy.name}")
        
        # Initialize trading engine
        engine = LiveTradingEngine(strategy, data_client, trader_client)
        
        # Start trading
        engine.start()
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please set your API keys in environment variables:")
        print("  export XTDATA_API_KEY='your_xtdata_key'")
        print("  export XTTRADER_API_KEY='your_xttrader_key'")
        print("  export XTTRADER_SECRET_KEY='your_xttrader_secret'")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()