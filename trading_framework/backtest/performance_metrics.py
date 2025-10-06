"""
Performance metrics calculation for backtesting results.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger


class PerformanceMetrics:
    """
    Comprehensive performance metrics for trading strategy backtests.
    
    Calculates various performance metrics including:
    - Total return, annualized return
    - Maximum drawdown
    - Sharpe ratio, Sortino ratio
    - Win rate, profit factor
    - Volatility metrics
    - Risk-adjusted returns
    """
    
    def __init__(
        self, 
        trades: List,  # List of Trade objects
        portfolio_history: Optional[List[Dict[str, Any]]] = None,
        initial_capital: float = 100000,
        risk_free_rate: float = 0.02  # 2% annual risk-free rate
    ):
        """
        Initialize performance metrics calculator.
        
        Args:
            trades: List of completed trades
            portfolio_history: Portfolio value history over time
            initial_capital: Initial capital
            risk_free_rate: Annual risk-free rate for Sharpe ratio calculation
        """
        self.trades = trades
        self.portfolio_history = portfolio_history or []
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate
        
        # Calculate derived metrics
        self._calculate_metrics()
    
    def _calculate_metrics(self) -> None:
        """Calculate all performance metrics."""
        # Basic metrics
        self.total_trades = len(self.trades)
        self.winning_trades = len([t for t in self.trades if t.is_profitable])
        self.losing_trades = self.total_trades - self.winning_trades
        
        # Return metrics
        self._calculate_return_metrics()
        
        # Risk metrics
        self._calculate_risk_metrics()
        
        # Trade statistics
        self._calculate_trade_statistics()
        
        # Drawdown metrics
        self._calculate_drawdown_metrics()
    
    def _calculate_return_metrics(self) -> None:
        """Calculate return-related metrics."""
        if not self.portfolio_history:
            self.total_return = 0.0
            self.annualized_return = 0.0
            self.final_value = self.initial_capital
            return
        
        # Get final portfolio value
        self.final_value = self.portfolio_history[-1]['total_value']
        
        # Total return
        self.total_return = (self.final_value - self.initial_capital) / self.initial_capital
        
        # Annualized return
        if len(self.portfolio_history) > 1:
            start_date = self.portfolio_history[0]['timestamp']
            end_date = self.portfolio_history[-1]['timestamp']
            days = (end_date - start_date).days
            years = days / 365.25
            
            if years > 0:
                self.annualized_return = (self.final_value / self.initial_capital) ** (1 / years) - 1
            else:
                self.annualized_return = 0.0
        else:
            self.annualized_return = 0.0
    
    def _calculate_risk_metrics(self) -> None:
        """Calculate risk-related metrics."""
        if not self.portfolio_history or len(self.portfolio_history) < 2:
            self.volatility = 0.0
            self.sharpe_ratio = 0.0
            self.sortino_ratio = 0.0
            return
        
        # Calculate daily returns
        values = [h['total_value'] for h in self.portfolio_history]
        returns = pd.Series(values).pct_change().dropna()
        
        if len(returns) == 0:
            self.volatility = 0.0
            self.sharpe_ratio = 0.0
            self.sortino_ratio = 0.0
            return
        
        # Volatility (annualized)
        self.volatility = returns.std() * np.sqrt(252)  # Assuming daily data
        
        # Sharpe ratio
        if self.volatility > 0:
            excess_return = self.annualized_return - self.risk_free_rate
            self.sharpe_ratio = excess_return / self.volatility
        else:
            self.sharpe_ratio = 0.0
        
        # Sortino ratio (using downside deviation)
        negative_returns = returns[returns < 0]
        if len(negative_returns) > 0:
            downside_deviation = negative_returns.std() * np.sqrt(252)
            if downside_deviation > 0:
                excess_return = self.annualized_return - self.risk_free_rate
                self.sortino_ratio = excess_return / downside_deviation
            else:
                self.sortino_ratio = 0.0
        else:
            self.sortino_ratio = float('inf') if self.annualized_return > self.risk_free_rate else 0.0
    
    def _calculate_trade_statistics(self) -> None:
        """Calculate trade-related statistics."""
        if not self.trades:
            self.win_rate = 0.0
            self.profit_factor = 0.0
            self.avg_win = 0.0
            self.avg_loss = 0.0
            self.largest_win = 0.0
            self.largest_loss = 0.0
            self.avg_trade_duration = 0.0
            return
        
        # Win rate
        self.win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0.0
        
        # Profit factor
        total_profit = sum(t.pnl for t in self.trades if t.is_profitable)
        total_loss = abs(sum(t.pnl for t in self.trades if not t.is_profitable))
        
        if total_loss > 0:
            self.profit_factor = total_profit / total_loss
        else:
            self.profit_factor = float('inf') if total_profit > 0 else 0.0
        
        # Average win/loss
        winning_trades_pnl = [t.pnl for t in self.trades if t.is_profitable]
        losing_trades_pnl = [t.pnl for t in self.trades if not t.is_profitable]
        
        self.avg_win = np.mean(winning_trades_pnl) if winning_trades_pnl else 0.0
        self.avg_loss = np.mean(losing_trades_pnl) if losing_trades_pnl else 0.0
        
        # Largest win/loss
        self.largest_win = max(winning_trades_pnl) if winning_trades_pnl else 0.0
        self.largest_loss = min(losing_trades_pnl) if losing_trades_pnl else 0.0
        
        # Average trade duration
        durations = [t.duration.total_seconds() / 3600 for t in self.trades]  # Hours
        self.avg_trade_duration = np.mean(durations) if durations else 0.0
    
    def _calculate_drawdown_metrics(self) -> None:
        """Calculate drawdown-related metrics."""
        if not self.portfolio_history:
            self.max_drawdown = 0.0
            self.max_drawdown_duration = 0.0
            return
        
        # Calculate running maximum and drawdown
        values = [h['total_value'] for h in self.portfolio_history]
        df = pd.DataFrame({
            'value': values,
            'timestamp': [h['timestamp'] for h in self.portfolio_history]
        })
        
        df['running_max'] = df['value'].expanding().max()
        df['drawdown'] = (df['value'] - df['running_max']) / df['running_max']
        
        # Maximum drawdown
        self.max_drawdown = abs(df['drawdown'].min())
        
        # Maximum drawdown duration
        drawdown_periods = []
        in_drawdown = False
        start_idx = 0
        
        for i, dd in enumerate(df['drawdown']):
            if dd < 0 and not in_drawdown:
                # Start of drawdown
                in_drawdown = True
                start_idx = i
            elif dd == 0 and in_drawdown:
                # End of drawdown
                in_drawdown = False
                duration = (df.iloc[i]['timestamp'] - df.iloc[start_idx]['timestamp']).days
                drawdown_periods.append(duration)
        
        # If still in drawdown at the end
        if in_drawdown:
            duration = (df.iloc[-1]['timestamp'] - df.iloc[start_idx]['timestamp']).days
            drawdown_periods.append(duration)
        
        self.max_drawdown_duration = max(drawdown_periods) if drawdown_periods else 0.0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all performance metrics."""
        return {
            # Return metrics
            'total_return': self.total_return,
            'annualized_return': self.annualized_return,
            'final_value': self.final_value,
            
            # Risk metrics
            'volatility': self.volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_duration': self.max_drawdown_duration,
            
            # Trade statistics
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'largest_win': self.largest_win,
            'largest_loss': self.largest_loss,
            'avg_trade_duration': self.avg_trade_duration,
        }
    
    def print_summary(self) -> None:
        """Print formatted summary of performance metrics."""
        print("=" * 60)
        print("PERFORMANCE SUMMARY")
        print("=" * 60)
        
        print(f"Initial Capital:        ${self.initial_capital:,.2f}")
        print(f"Final Value:           ${self.final_value:,.2f}")
        print(f"Total Return:          {self.total_return:.2%}")
        print(f"Annualized Return:     {self.annualized_return:.2%}")
        print()
        
        print("RISK METRICS")
        print("-" * 30)
        print(f"Volatility:            {self.volatility:.2%}")
        print(f"Sharpe Ratio:          {self.sharpe_ratio:.2f}")
        print(f"Sortino Ratio:         {self.sortino_ratio:.2f}")
        print(f"Max Drawdown:          {self.max_drawdown:.2%}")
        print(f"Max DD Duration:       {self.max_drawdown_duration:.0f} days")
        print()
        
        print("TRADE STATISTICS")
        print("-" * 30)
        print(f"Total Trades:          {self.total_trades}")
        print(f"Winning Trades:        {self.winning_trades}")
        print(f"Losing Trades:         {self.losing_trades}")
        print(f"Win Rate:              {self.win_rate:.2%}")
        print(f"Profit Factor:         {self.profit_factor:.2f}")
        print(f"Average Win:           ${self.avg_win:.2f}")
        print(f"Average Loss:          ${self.avg_loss:.2f}")
        print(f"Largest Win:           ${self.largest_win:.2f}")
        print(f"Largest Loss:          ${self.largest_loss:.2f}")
        print(f"Avg Trade Duration:    {self.avg_trade_duration:.1f} hours")
        print("=" * 60)
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert portfolio history to DataFrame for analysis."""
        if not self.portfolio_history:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.portfolio_history)
        df = df.set_index('timestamp')
        
        # Calculate additional columns
        df['returns'] = df['total_value'].pct_change()
        df['cumulative_returns'] = (df['total_value'] / self.initial_capital) - 1
        df['running_max'] = df['total_value'].expanding().max()
        df['drawdown'] = (df['total_value'] - df['running_max']) / df['running_max']
        
        return df
    
    def get_monthly_returns(self) -> pd.Series:
        """Get monthly returns series."""
        df = self.to_dataframe()
        if df.empty:
            return pd.Series()
        
        monthly = df['total_value'].resample('M').last()
        monthly_returns = monthly.pct_change().dropna()
        
        return monthly_returns
    
    def get_yearly_returns(self) -> pd.Series:
        """Get yearly returns series."""
        df = self.to_dataframe()
        if df.empty:
            return pd.Series()
        
        yearly = df['total_value'].resample('Y').last()
        yearly_returns = yearly.pct_change().dropna()
        
        return yearly_returns
    
    def compare_to_benchmark(self, benchmark_returns: pd.Series) -> Dict[str, float]:
        """
        Compare strategy performance to a benchmark.
        
        Args:
            benchmark_returns: Benchmark returns series
            
        Returns:
            Dictionary with comparison metrics
        """
        strategy_df = self.to_dataframe()
        if strategy_df.empty:
            return {}
        
        # Align dates
        strategy_returns = strategy_df['returns'].dropna()
        common_dates = strategy_returns.index.intersection(benchmark_returns.index)
        
        if len(common_dates) == 0:
            return {}
        
        strategy_aligned = strategy_returns.loc[common_dates]
        benchmark_aligned = benchmark_returns.loc[common_dates]
        
        # Calculate metrics
        strategy_total_return = (1 + strategy_aligned).prod() - 1
        benchmark_total_return = (1 + benchmark_aligned).prod() - 1
        
        excess_returns = strategy_aligned - benchmark_aligned
        tracking_error = excess_returns.std() * np.sqrt(252)
        
        information_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() > 0 else 0
        
        # Beta calculation
        if benchmark_aligned.var() > 0:
            beta = np.cov(strategy_aligned, benchmark_aligned)[0, 1] / benchmark_aligned.var()
        else:
            beta = 0
        
        return {
            'strategy_return': strategy_total_return,
            'benchmark_return': benchmark_total_return,
            'excess_return': strategy_total_return - benchmark_total_return,
            'tracking_error': tracking_error,
            'information_ratio': information_ratio,
            'beta': beta
        }