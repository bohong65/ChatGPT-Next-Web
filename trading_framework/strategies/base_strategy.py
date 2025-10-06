"""
Base strategy class that all trading strategies should inherit from.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from datetime import datetime
from loguru import logger


class Signal:
    """Represents a trading signal."""
    
    def __init__(
        self, 
        symbol: str, 
        action: str, 
        quantity: float, 
        price: Optional[float] = None,
        timestamp: Optional[datetime] = None,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a trading signal.
        
        Args:
            symbol: Trading symbol
            action: 'BUY', 'SELL', or 'HOLD'
            quantity: Number of shares/units
            price: Target price (None for market orders)
            timestamp: Signal generation time
            confidence: Signal confidence (0.0 to 1.0)
            metadata: Additional signal information
        """
        self.symbol = symbol
        self.action = action.upper()
        self.quantity = quantity
        self.price = price
        self.timestamp = timestamp or datetime.now()
        self.confidence = confidence
        self.metadata = metadata or {}
        
        if self.action not in ['BUY', 'SELL', 'HOLD']:
            raise ValueError(f"Invalid action: {self.action}")
    
    def __repr__(self):
        return f"Signal({self.symbol}, {self.action}, {self.quantity}, {self.price})"


class Position:
    """Represents a trading position."""
    
    def __init__(self, symbol: str, quantity: float, entry_price: float, entry_time: datetime):
        """
        Initialize a position.
        
        Args:
            symbol: Trading symbol
            quantity: Position size (positive for long, negative for short)
            entry_price: Entry price
            entry_time: Entry timestamp
        """
        self.symbol = symbol
        self.quantity = quantity
        self.entry_price = entry_price
        self.entry_time = entry_time
        self.current_price = entry_price
        self.last_update = entry_time
    
    @property
    def market_value(self) -> float:
        """Current market value of the position."""
        return self.quantity * self.current_price
    
    @property
    def pnl(self) -> float:
        """Unrealized profit/loss."""
        return (self.current_price - self.entry_price) * self.quantity
    
    @property
    def pnl_pct(self) -> float:
        """Unrealized profit/loss percentage."""
        if self.entry_price == 0:
            return 0.0
        return (self.current_price - self.entry_price) / self.entry_price
    
    def update_price(self, price: float, timestamp: datetime):
        """Update current price and timestamp."""
        self.current_price = price
        self.last_update = timestamp
    
    def __repr__(self):
        return f"Position({self.symbol}, {self.quantity}, {self.current_price}, PnL: {self.pnl:.2f})"


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    All trading strategies should inherit from this class and implement
    the required abstract methods.
    """
    
    def __init__(self, name: str, parameters: Optional[Dict[str, Any]] = None):
        """
        Initialize base strategy.
        
        Args:
            name: Strategy name
            parameters: Strategy parameters dictionary
        """
        self.name = name
        self.parameters = parameters or {}
        self.positions: Dict[str, Position] = {}
        self.signals_history: List[Signal] = []
        self.is_initialized = False
        
        logger.info(f"Initialized strategy: {self.name}")
    
    @abstractmethod
    def initialize(self, data: pd.DataFrame) -> None:
        """
        Initialize strategy with historical data.
        
        This method is called once before strategy execution begins.
        Use it to precompute indicators or set up internal state.
        
        Args:
            data: Historical market data DataFrame
        """
        pass
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame, timestamp: datetime) -> List[Signal]:
        """
        Generate trading signals based on current market data.
        
        Args:
            data: Current market data (may include historical context)
            timestamp: Current timestamp
            
        Returns:
            List of trading signals
        """
        pass
    
    def on_data(self, data: pd.DataFrame, timestamp: datetime) -> List[Signal]:
        """
        Called when new market data is available.
        
        Args:
            data: Market data DataFrame
            timestamp: Data timestamp
            
        Returns:
            List of trading signals
        """
        if not self.is_initialized:
            self.initialize(data)
            self.is_initialized = True
        
        signals = self.generate_signals(data, timestamp)
        
        # Store signals in history
        self.signals_history.extend(signals)
        
        # Log signals
        for signal in signals:
            logger.info(f"Generated signal: {signal}")
        
        return signals
    
    def update_position(self, symbol: str, quantity: float, price: float, timestamp: datetime):
        """
        Update position for a symbol.
        
        Args:
            symbol: Trading symbol
            quantity: New position quantity
            price: Current price
            timestamp: Update timestamp
        """
        if symbol in self.positions:
            if quantity == 0:
                # Close position
                del self.positions[symbol]
                logger.info(f"Closed position in {symbol}")
            else:
                # Update existing position
                self.positions[symbol].quantity = quantity
                self.positions[symbol].update_price(price, timestamp)
        else:
            if quantity != 0:
                # Open new position
                self.positions[symbol] = Position(symbol, quantity, price, timestamp)
                logger.info(f"Opened position in {symbol}: {quantity} @ {price}")
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get current position for a symbol."""
        return self.positions.get(symbol)
    
    def get_portfolio_value(self) -> float:
        """Get total portfolio value."""
        return sum(pos.market_value for pos in self.positions.values())
    
    def get_portfolio_pnl(self) -> float:
        """Get total portfolio PnL."""
        return sum(pos.pnl for pos in self.positions.values())
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Get strategy parameter."""
        return self.parameters.get(key, default)
    
    def set_parameter(self, key: str, value: Any) -> None:
        """Set strategy parameter."""
        self.parameters[key] = value
        logger.debug(f"Set parameter {key} = {value}")
    
    def reset(self) -> None:
        """Reset strategy state."""
        self.positions.clear()
        self.signals_history.clear()
        self.is_initialized = False
        logger.info(f"Reset strategy: {self.name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get strategy statistics."""
        return {
            'name': self.name,
            'parameters': self.parameters,
            'positions_count': len(self.positions),
            'signals_count': len(self.signals_history),
            'portfolio_value': self.get_portfolio_value(),
            'portfolio_pnl': self.get_portfolio_pnl()
        }
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', positions={len(self.positions)})"