"""
Helper functions for the trading framework.
"""

import re
import math
from typing import Optional, Union
from loguru import logger

from ..config import get_config


def calculate_position_size(
    account_value: float,
    risk_per_trade: float,
    entry_price: float,
    stop_loss_price: float,
    max_position_size: Optional[float] = None
) -> float:
    """
    Calculate position size based on risk management rules.
    
    Args:
        account_value: Total account value
        risk_per_trade: Risk per trade as percentage (e.g., 0.02 for 2%)
        entry_price: Entry price for the position
        stop_loss_price: Stop loss price
        max_position_size: Maximum position size as percentage of account
        
    Returns:
        Position size (number of shares/units)
    """
    if max_position_size is None:
        config = get_config()
        max_position_size = config.get('risk_management', {}).get('max_position_size', 0.1)
    
    # Calculate risk per share
    risk_per_share = abs(entry_price - stop_loss_price)
    
    if risk_per_share == 0:
        logger.warning("Risk per share is zero, cannot calculate position size")
        return 0
    
    # Calculate position size based on risk
    risk_amount = account_value * risk_per_trade
    position_size = risk_amount / risk_per_share
    
    # Apply maximum position size limit
    max_shares = (account_value * max_position_size) / entry_price
    position_size = min(position_size, max_shares)
    
    # Round down to avoid exceeding limits
    position_size = math.floor(position_size)
    
    logger.debug(f"Position size calculated: {position_size} shares")
    return position_size


def validate_symbol(symbol: str) -> bool:
    """
    Validate trading symbol format.
    
    Args:
        symbol: Trading symbol to validate
        
    Returns:
        True if symbol is valid
    """
    if not symbol or not isinstance(symbol, str):
        return False
    
    # Remove whitespace
    symbol = symbol.strip().upper()
    
    # Basic validation patterns
    patterns = [
        r'^[A-Z]{1,6}$',                    # US stocks (1-6 letters)
        r'^[A-Z]{1,6}\.[A-Z]{2}$',          # International stocks with exchange
        r'^\d{6}\.[A-Z]{2}$',               # Chinese stocks (6 digits + exchange)
        r'^[A-Z]{3}USD$',                   # Forex pairs
        r'^[A-Z]+\d{4}$',                   # Futures contracts
    ]
    
    for pattern in patterns:
        if re.match(pattern, symbol):
            return True
    
    logger.warning(f"Invalid symbol format: {symbol}")
    return False


def format_currency(amount: float, currency: str = 'USD', decimals: int = 2) -> str:
    """
    Format currency amount for display.
    
    Args:
        amount: Amount to format
        currency: Currency code
        decimals: Number of decimal places
        
    Returns:
        Formatted currency string
    """
    if currency.upper() == 'USD':
        symbol = '$'
    elif currency.upper() == 'EUR':
        symbol = '€'
    elif currency.upper() == 'GBP':
        symbol = '£'
    elif currency.upper() == 'JPY':
        symbol = '¥'
        decimals = 0  # JPY typically has no decimals
    elif currency.upper() == 'CNY':
        symbol = '¥'
    else:
        symbol = currency + ' '
    
    formatted = f"{amount:,.{decimals}f}"
    
    if currency.upper() in ['USD', 'EUR', 'GBP', 'JPY', 'CNY']:
        return f"{symbol}{formatted}"
    else:
        return f"{formatted} {currency}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format percentage for display.
    
    Args:
        value: Percentage value (e.g., 0.025 for 2.5%)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.{decimals}f}%"


def validate_price(price: Union[float, int, str]) -> bool:
    """
    Validate price value.
    
    Args:
        price: Price to validate
        
    Returns:
        True if price is valid
    """
    try:
        price_float = float(price)
        return price_float > 0 and math.isfinite(price_float)
    except (ValueError, TypeError):
        return False


def validate_quantity(quantity: Union[float, int, str]) -> bool:
    """
    Validate quantity value.
    
    Args:
        quantity: Quantity to validate
        
    Returns:
        True if quantity is valid
    """
    try:
        quantity_float = float(quantity)
        return quantity_float > 0 and math.isfinite(quantity_float)
    except (ValueError, TypeError):
        return False


def round_to_tick_size(price: float, tick_size: float = 0.01) -> float:
    """
    Round price to the nearest tick size.
    
    Args:
        price: Price to round
        tick_size: Minimum price increment
        
    Returns:
        Rounded price
    """
    if tick_size <= 0:
        return price
    
    return round(price / tick_size) * tick_size


def calculate_fees(trade_value: float, commission_rate: float = 0.001) -> float:
    """
    Calculate trading fees.
    
    Args:
        trade_value: Value of the trade
        commission_rate: Commission rate as decimal
        
    Returns:
        Total fees
    """
    return trade_value * commission_rate


def is_market_hours(exchange: str = 'US') -> bool:
    """
    Check if market is currently open.
    
    Args:
        exchange: Exchange to check ('US', 'EU', 'ASIA')
        
    Returns:
        True if market is open
    """
    from datetime import datetime, time
    import pytz
    
    now_utc = datetime.now(pytz.UTC)
    
    if exchange.upper() == 'US':
        # NYSE/NASDAQ: 9:30 AM - 4:00 PM ET
        et_tz = pytz.timezone('US/Eastern')
        now_et = now_utc.astimezone(et_tz)
        
        # Check if weekday
        if now_et.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        market_open = time(9, 30)
        market_close = time(16, 0)
        current_time = now_et.time()
        
        return market_open <= current_time <= market_close
    
    elif exchange.upper() == 'EU':
        # European markets: 8:00 AM - 4:30 PM CET
        cet_tz = pytz.timezone('Europe/Berlin')
        now_cet = now_utc.astimezone(cet_tz)
        
        if now_cet.weekday() >= 5:
            return False
        
        market_open = time(8, 0)
        market_close = time(16, 30)
        current_time = now_cet.time()
        
        return market_open <= current_time <= market_close
    
    elif exchange.upper() == 'ASIA':
        # Asian markets (simplified): 9:00 AM - 3:00 PM JST
        jst_tz = pytz.timezone('Asia/Tokyo')
        now_jst = now_utc.astimezone(jst_tz)
        
        if now_jst.weekday() >= 5:
            return False
        
        market_open = time(9, 0)
        market_close = time(15, 0)
        current_time = now_jst.time()
        
        return market_open <= current_time <= market_close
    
    # Default to always open for unknown exchanges
    return True


def get_trading_calendar(exchange: str = 'US', year: Optional[int] = None):
    """
    Get trading calendar for an exchange.
    
    Args:
        exchange: Exchange code
        year: Year to get calendar for (current year if None)
        
    Returns:
        List of trading days
    """
    # This is a simplified implementation
    # In production, you would use a proper trading calendar library
    
    from datetime import datetime, date
    import calendar
    
    if year is None:
        year = datetime.now().year
    
    trading_days = []
    
    for month in range(1, 13):
        for day in range(1, calendar.monthrange(year, month)[1] + 1):
            current_date = date(year, month, day)
            
            # Skip weekends
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                # Skip major holidays (simplified)
                if not _is_holiday(current_date, exchange):
                    trading_days.append(current_date)
    
    return trading_days


def _is_holiday(date_obj: date, exchange: str) -> bool:
    """Check if a date is a trading holiday."""
    # Simplified holiday checking
    # In production, use a proper holiday calendar
    
    if exchange.upper() == 'US':
        # Major US holidays (simplified)
        holidays = [
            (1, 1),   # New Year's Day
            (7, 4),   # Independence Day  
            (12, 25)  # Christmas
        ]
        
        return (date_obj.month, date_obj.day) in holidays
    
    return False