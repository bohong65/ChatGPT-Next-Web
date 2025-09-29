"""
Backtesting engine for simulating trading strategies on historical data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from loguru import logger

from ..strategies.base_strategy import BaseStrategy, Signal
from ..data import XTDataClient
from .performance_metrics import PerformanceMetrics


class Trade:
    """Represents a completed trade."""
    
    def __init__(
        self, 
        symbol: str, 
        entry_time: datetime, 
        exit_time: datetime,
        entry_price: float, 
        exit_price: float, 
        quantity: float,
        commission: float = 0.0
    ):
        self.symbol = symbol
        self.entry_time = entry_time
        self.exit_time = exit_time
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.quantity = quantity
        self.commission = commission
        self.duration = exit_time - entry_time
    
    @property
    def pnl(self) -> float:
        """Profit/Loss of the trade."""
        return (self.exit_price - self.entry_price) * self.quantity - self.commission
    
    @property
    def pnl_pct(self) -> float:
        """Profit/Loss percentage."""
        if self.entry_price == 0:
            return 0.0
        return (self.exit_price - self.entry_price) / self.entry_price
    
    @property
    def is_profitable(self) -> bool:
        """Whether the trade was profitable."""
        return self.pnl > 0
    
    def __repr__(self):
        return f"Trade({self.symbol}, {self.pnl:.2f}, {self.pnl_pct:.2%})"


class BacktestEngine:
    """
    Backtesting engine for simulating trading strategies on historical data.
    
    Features:
    - Simulate trades based on strategy signals
    - Track portfolio performance over time
    - Calculate comprehensive performance metrics
    - Support for transaction costs and slippage
    - Position sizing and risk management
    """
    
    def __init__(
        self, 
        strategy: BaseStrategy,
        initial_capital: float = 100000,
        commission: float = 0.001,  # 0.1% commission
        slippage: float = 0.0005,   # 0.05% slippage
        data_client: Optional[XTDataClient] = None
    ):
        """
        Initialize backtest engine.
        
        Args:
            strategy: Trading strategy to backtest
            initial_capital: Starting capital
            commission: Commission rate (as fraction)
            slippage: Slippage rate (as fraction)
            data_client: Data client for fetching historical data
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.data_client = data_client
        
        # Backtest state
        self.current_capital = initial_capital
        self.positions = {}  # symbol -> quantity
        self.trades = []
        self.portfolio_history = []
        self.signal_history = []
        
        logger.info(f"Initialized backtest engine with {initial_capital:,.2f} capital")
    
    def run(
        self, 
        start_date: str, 
        end_date: str,
        symbols: Optional[List[str]] = None,
        data: Optional[pd.DataFrame] = None
    ) -> PerformanceMetrics:
        """
        Run backtest over specified date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            symbols: List of symbols to trade (if None, uses strategy default)
            data: Pre-loaded data (if None, fetches from data_client)
            
        Returns:
            Performance metrics object
        """
        logger.info(f"Starting backtest from {start_date} to {end_date}")
        
        # Reset state
        self._reset_backtest()
        
        # Get historical data
        if data is None:
            data = self._fetch_historical_data(start_date, end_date, symbols)
        
        if data.empty:
            logger.error("No historical data available for backtest")
            return PerformanceMetrics([])
        
        # Initialize strategy
        self.strategy.reset()
        self.strategy.initialize(data)
        
        # Run simulation
        self._simulate_trading(data, start_date, end_date)
        
        # Calculate performance metrics
        metrics = self._calculate_performance_metrics()
        
        logger.info(f"Backtest completed. Total return: {metrics.total_return:.2%}")
        return metrics
    
    def _reset_backtest(self) -> None:
        """Reset backtest state."""
        self.current_capital = self.initial_capital
        self.positions.clear()
        self.trades.clear()
        self.portfolio_history.clear()
        self.signal_history.clear()
    
    def _fetch_historical_data(
        self, 
        start_date: str, 
        end_date: str, 
        symbols: Optional[List[str]]
    ) -> pd.DataFrame:
        """Fetch historical data for backtesting."""
        if not self.data_client:
            logger.error("No data client available for fetching historical data")
            return pd.DataFrame()
        
        if not symbols:
            symbols = ['AAPL']  # Default symbol
        
        all_data = []
        
        for symbol in symbols:
            try:
                symbol_data = self.data_client.get_historical_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    interval='1d'
                )
                
                if not symbol_data.empty:
                    symbol_data['symbol'] = symbol
                    all_data.append(symbol_data)
                    
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
        
        if all_data:
            # Combine all symbol data
            combined_data = pd.concat(all_data)
            combined_data = combined_data.set_index(['symbol', combined_data.index])
            return combined_data
        
        return pd.DataFrame()
    
    def _simulate_trading(self, data: pd.DataFrame, start_date: str, end_date: str) -> None:
        """Simulate trading over the historical data."""
        logger.info("Starting trading simulation")
        
        # Get unique timestamps
        if isinstance(data.index, pd.MultiIndex):
            timestamps = sorted(data.index.get_level_values(-1).unique())
        else:
            timestamps = sorted(data.index.unique())
        
        # Filter timestamps to date range
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        timestamps = [ts for ts in timestamps if start_dt <= ts <= end_dt]
        
        for i, timestamp in enumerate(timestamps):
            try:
                # Get data up to current timestamp
                if isinstance(data.index, pd.MultiIndex):
                    current_data = data.loc[data.index.get_level_values(-1) <= timestamp]
                else:
                    current_data = data.loc[data.index <= timestamp]
                
                # Generate signals
                signals = self.strategy.on_data(current_data, timestamp)
                
                # Execute signals
                for signal in signals:
                    self._execute_signal(signal, timestamp, current_data)
                
                # Record portfolio state
                self._record_portfolio_state(timestamp, current_data)
                
                if i % 100 == 0:
                    logger.debug(f"Processed {i+1}/{len(timestamps)} timestamps")
                    
            except Exception as e:
                logger.error(f"Error processing timestamp {timestamp}: {e}")
        
        # Close all remaining positions at the end
        self._close_all_positions(timestamps[-1], data)
        
        logger.info(f"Simulation completed. Executed {len(self.trades)} trades")
    
    def _execute_signal(self, signal: Signal, timestamp: datetime, data: pd.DataFrame) -> None:
        """Execute a trading signal."""
        try:
            # Get current price (with slippage)
            execution_price = self._get_execution_price(signal, data)
            if execution_price is None:
                logger.warning(f"Could not get execution price for {signal.symbol}")
                return
            
            # Calculate transaction cost
            trade_value = signal.quantity * execution_price
            commission_cost = trade_value * self.commission
            
            if signal.action == 'BUY':
                self._execute_buy(signal, execution_price, commission_cost, timestamp)
            elif signal.action == 'SELL':
                self._execute_sell(signal, execution_price, commission_cost, timestamp)
                
            # Store signal in history
            self.signal_history.append({
                'timestamp': timestamp,
                'signal': signal,
                'execution_price': execution_price,
                'commission': commission_cost
            })
            
        except Exception as e:
            logger.error(f"Error executing signal {signal}: {e}")
    
    def _get_execution_price(self, signal: Signal, data: pd.DataFrame) -> Optional[float]:
        """Get execution price with slippage applied."""
        try:
            if signal.price is not None:
                # Use signal price if specified
                base_price = signal.price
            else:
                # Get current market price
                if isinstance(data.index, pd.MultiIndex):
                    symbol_data = data.xs(signal.symbol, level='symbol')
                    if not symbol_data.empty and 'close' in symbol_data.columns:
                        base_price = float(symbol_data['close'].iloc[-1])
                    else:
                        return None
                else:
                    if 'close' in data.columns and not data.empty:
                        base_price = float(data['close'].iloc[-1])
                    else:
                        return None
            
            # Apply slippage
            if signal.action == 'BUY':
                execution_price = base_price * (1 + self.slippage)
            else:
                execution_price = base_price * (1 - self.slippage)
            
            return execution_price
            
        except Exception as e:
            logger.error(f"Error calculating execution price: {e}")
            return None
    
    def _execute_buy(self, signal: Signal, price: float, commission: float, timestamp: datetime) -> None:
        """Execute buy order."""
        trade_value = signal.quantity * price + commission
        
        if trade_value > self.current_capital:
            logger.warning(f"Insufficient capital for buy order: {trade_value:.2f} > {self.current_capital:.2f}")
            return
        
        # Update capital
        self.current_capital -= trade_value
        
        # Update position
        if signal.symbol in self.positions:
            self.positions[signal.symbol] += signal.quantity
        else:
            self.positions[signal.symbol] = signal.quantity
        
        # Update strategy position
        self.strategy.update_position(signal.symbol, self.positions[signal.symbol], price, timestamp)
        
        logger.debug(f"Executed BUY: {signal.quantity} {signal.symbol} @ {price:.2f}")
    
    def _execute_sell(self, signal: Signal, price: float, commission: float, timestamp: datetime) -> None:
        """Execute sell order."""
        current_position = self.positions.get(signal.symbol, 0)
        
        # Determine actual quantity to sell
        sell_quantity = min(signal.quantity, current_position)
        
        if sell_quantity <= 0:
            logger.warning(f"No position to sell for {signal.symbol}")
            return
        
        # Calculate trade for completed trades tracking
        if current_position > 0:
            # This is closing a long position - create trade record
            strategy_position = self.strategy.get_position(signal.symbol)
            if strategy_position:
                trade = Trade(
                    symbol=signal.symbol,
                    entry_time=strategy_position.entry_time,
                    exit_time=timestamp,
                    entry_price=strategy_position.entry_price,
                    exit_price=price,
                    quantity=sell_quantity,
                    commission=commission
                )
                self.trades.append(trade)
        
        # Update capital
        trade_value = sell_quantity * price - commission
        self.current_capital += trade_value
        
        # Update position
        self.positions[signal.symbol] -= sell_quantity
        if self.positions[signal.symbol] <= 0:
            del self.positions[signal.symbol]
        
        # Update strategy position
        remaining_position = self.positions.get(signal.symbol, 0)
        self.strategy.update_position(signal.symbol, remaining_position, price, timestamp)
        
        logger.debug(f"Executed SELL: {sell_quantity} {signal.symbol} @ {price:.2f}")
    
    def _record_portfolio_state(self, timestamp: datetime, data: pd.DataFrame) -> None:
        """Record current portfolio state."""
        try:
            # Calculate position values
            position_value = 0
            for symbol, quantity in self.positions.items():
                try:
                    if isinstance(data.index, pd.MultiIndex):
                        symbol_data = data.xs(symbol, level='symbol')
                        if not symbol_data.empty and 'close' in symbol_data.columns:
                            current_price = float(symbol_data['close'].iloc[-1])
                            position_value += quantity * current_price
                    else:
                        if 'close' in data.columns and not data.empty:
                            current_price = float(data['close'].iloc[-1])
                            position_value += quantity * current_price
                except Exception:
                    continue
            
            total_value = self.current_capital + position_value
            
            self.portfolio_history.append({
                'timestamp': timestamp,
                'capital': self.current_capital,
                'position_value': position_value,
                'total_value': total_value,
                'positions': dict(self.positions)
            })
            
        except Exception as e:
            logger.error(f"Error recording portfolio state: {e}")
    
    def _close_all_positions(self, timestamp: datetime, data: pd.DataFrame) -> None:
        """Close all remaining positions at the end of backtest."""
        for symbol in list(self.positions.keys()):
            if self.positions[symbol] > 0:
                # Create sell signal to close position
                sell_signal = Signal(
                    symbol=symbol,
                    action='SELL',
                    quantity=self.positions[symbol],
                    timestamp=timestamp
                )
                self._execute_signal(sell_signal, timestamp, data)
    
    def _calculate_performance_metrics(self) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics."""
        return PerformanceMetrics(
            trades=self.trades,
            portfolio_history=self.portfolio_history,
            initial_capital=self.initial_capital
        )
    
    def get_backtest_summary(self) -> Dict[str, Any]:
        """Get summary of backtest results."""
        metrics = self._calculate_performance_metrics()
        
        return {
            'initial_capital': self.initial_capital,
            'final_capital': self.current_capital,
            'total_trades': len(self.trades),
            'total_return': metrics.total_return,
            'max_drawdown': metrics.max_drawdown,
            'sharpe_ratio': metrics.sharpe_ratio,
            'win_rate': metrics.win_rate,
            'profit_factor': metrics.profit_factor,
            'positions': dict(self.positions),
            'signals_generated': len(self.signal_history)
        }