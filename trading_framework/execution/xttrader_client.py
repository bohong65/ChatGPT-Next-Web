"""
XTTrader API Client for executing real trading orders.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from loguru import logger

from ..config import get_config


class OrderType(Enum):
    """Order types supported by XTTrader."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Order sides."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status values."""
    PENDING = "pending"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Order:
    """Represents a trading order."""
    
    def __init__(
        self,
        symbol: str,
        side: Union[OrderSide, str],
        quantity: float,
        order_type: Union[OrderType, str] = OrderType.MARKET,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "GTC",  # Good Till Cancelled
        client_order_id: Optional[str] = None
    ):
        """
        Initialize order.
        
        Args:
            symbol: Trading symbol
            side: Order side (BUY/SELL)
            quantity: Order quantity
            order_type: Order type (MARKET/LIMIT/STOP/STOP_LIMIT)
            price: Limit price (required for LIMIT orders)
            stop_price: Stop price (required for STOP orders)
            time_in_force: Time in force (GTC, IOC, FOK)
            client_order_id: Client-provided order ID
        """
        self.symbol = symbol
        self.side = OrderSide(side) if isinstance(side, str) else side
        self.quantity = quantity
        self.order_type = OrderType(order_type) if isinstance(order_type, str) else order_type
        self.price = price
        self.stop_price = stop_price
        self.time_in_force = time_in_force
        self.client_order_id = client_order_id or f"order_{int(time.time() * 1000)}"
        
        # Order state
        self.order_id = None
        self.status = OrderStatus.PENDING
        self.filled_quantity = 0.0
        self.remaining_quantity = quantity
        self.avg_fill_price = 0.0
        self.created_time = datetime.now()
        self.updated_time = None
        
        # Validate order
        self._validate()
    
    def _validate(self):
        """Validate order parameters."""
        if self.quantity <= 0:
            raise ValueError("Order quantity must be positive")
        
        if self.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and self.price is None:
            raise ValueError(f"Price required for {self.order_type.value} orders")
        
        if self.order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and self.stop_price is None:
            raise ValueError(f"Stop price required for {self.order_type.value} orders")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert order to dictionary for API submission."""
        order_dict = {
            "symbol": self.symbol,
            "side": self.side.value,
            "quantity": self.quantity,
            "type": self.order_type.value,
            "timeInForce": self.time_in_force,
            "clientOrderId": self.client_order_id
        }
        
        if self.price is not None:
            order_dict["price"] = self.price
        
        if self.stop_price is not None:
            order_dict["stopPrice"] = self.stop_price
        
        return order_dict
    
    def update_status(self, status: str, filled_qty: float = 0, avg_price: float = 0):
        """Update order status and fill information."""
        self.status = OrderStatus(status)
        self.filled_quantity = filled_qty
        self.remaining_quantity = self.quantity - filled_qty
        if avg_price > 0:
            self.avg_fill_price = avg_price
        self.updated_time = datetime.now()
    
    def __repr__(self):
        return f"Order({self.symbol}, {self.side.value}, {self.quantity}, {self.order_type.value})"


class XTTraderClient:
    """
    Client for connecting to XTTrader API for order execution.
    
    Provides methods to:
    - Place market and limit orders
    - Cancel orders
    - Query order status
    - Manage positions
    - Get account information
    """
    
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize XTTrader client.
        
        Args:
            api_key: XTTrader API key. If None, will use config.
            secret_key: XTTrader secret key. If None, will use config.
            base_url: Base URL for XTTrader API. If None, will use config.
        """
        config = get_config()
        self.api_key = api_key or config.get('xttrader', {}).get('api_key')
        self.secret_key = secret_key or config.get('xttrader', {}).get('secret_key')
        self.base_url = base_url or config.get('xttrader', {}).get('base_url', 'https://api.xttrader.com')
        
        if not self.api_key or not self.secret_key:
            raise ValueError("XTTrader API key and secret key are required")
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key
        })
        
        # Order tracking
        self.active_orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        
        logger.info("XTTrader client initialized")
    
    def _sign_request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict[str, str]:
        """Generate signature for authenticated requests."""
        # Placeholder for signature generation
        # Real implementation would use HMAC with secret key
        timestamp = str(int(time.time() * 1000))
        
        # In real implementation, you would:
        # 1. Create query string from params
        # 2. Create string to sign: timestamp + method + endpoint + query_string
        # 3. Generate HMAC-SHA256 signature using secret key
        # 4. Return headers with signature
        
        return {
            'X-Timestamp': timestamp,
            'X-Signature': 'placeholder_signature'  # Replace with actual signature
        }
    
    def place_order(self, order: Order) -> bool:
        """
        Place a trading order.
        
        Args:
            order: Order object to place
            
        Returns:
            True if order was placed successfully
        """
        try:
            endpoint = '/api/v1/orders'
            headers = self._sign_request('POST', endpoint)
            self.session.headers.update(headers)
            
            order_data = order.to_dict()
            
            response = self.session.post(
                f'{self.base_url}{endpoint}',
                json=order_data
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('success'):
                order.order_id = result.get('orderId')
                order.status = OrderStatus.PENDING
                self.active_orders[order.order_id] = order
                
                logger.info(f"Order placed successfully: {order}")
                return True
            else:
                error_msg = result.get('message', 'Unknown error')
                logger.error(f"Failed to place order: {error_msg}")
                order.status = OrderStatus.REJECTED
                return False
                
        except requests.RequestException as e:
            logger.error(f"Error placing order: {e}")
            order.status = OrderStatus.REJECTED
            return False
        except Exception as e:
            logger.error(f"Unexpected error placing order: {e}")
            order.status = OrderStatus.REJECTED
            return False
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an active order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if order was cancelled successfully
        """
        try:
            endpoint = f'/api/v1/orders/{order_id}'
            headers = self._sign_request('DELETE', endpoint)
            self.session.headers.update(headers)
            
            response = self.session.delete(f'{self.base_url}{endpoint}')
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('success'):
                if order_id in self.active_orders:
                    order = self.active_orders[order_id]
                    order.status = OrderStatus.CANCELLED
                    order.updated_time = datetime.now()
                    del self.active_orders[order_id]
                    self.order_history.append(order)
                
                logger.info(f"Order cancelled successfully: {order_id}")
                return True
            else:
                error_msg = result.get('message', 'Unknown error')
                logger.error(f"Failed to cancel order: {error_msg}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Error cancelling order: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error cancelling order: {e}")
            return False
    
    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of an order.
        
        Args:
            order_id: Order ID to query
            
        Returns:
            Dictionary with order status information
        """
        try:
            endpoint = f'/api/v1/orders/{order_id}'
            headers = self._sign_request('GET', endpoint)
            self.session.headers.update(headers)
            
            response = self.session.get(f'{self.base_url}{endpoint}')
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('success'):
                order_data = result.get('data', {})
                
                # Update local order if we have it
                if order_id in self.active_orders:
                    order = self.active_orders[order_id]
                    order.update_status(
                        status=order_data.get('status', 'pending'),
                        filled_qty=float(order_data.get('filledQuantity', 0)),
                        avg_price=float(order_data.get('avgFillPrice', 0))
                    )
                
                return order_data
            else:
                logger.error(f"Failed to get order status: {result.get('message')}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error getting order status: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting order status: {e}")
            return None
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions.
        
        Returns:
            List of position dictionaries
        """
        try:
            endpoint = '/api/v1/positions'
            headers = self._sign_request('GET', endpoint)
            self.session.headers.update(headers)
            
            response = self.session.get(f'{self.base_url}{endpoint}')
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('success'):
                return result.get('data', [])
            else:
                logger.error(f"Failed to get positions: {result.get('message')}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"Error getting positions: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting positions: {e}")
            return []
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Get account information including balances.
        
        Returns:
            Dictionary with account information
        """
        try:
            endpoint = '/api/v1/account'
            headers = self._sign_request('GET', endpoint)
            self.session.headers.update(headers)
            
            response = self.session.get(f'{self.base_url}{endpoint}')
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('success'):
                return result.get('data', {})
            else:
                logger.error(f"Failed to get account info: {result.get('message')}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error getting account info: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting account info: {e}")
            return None
    
    def buy(self, symbol: str, quantity: float, price: Optional[float] = None) -> Optional[Order]:
        """
        Place a buy order.
        
        Args:
            symbol: Trading symbol
            quantity: Quantity to buy
            price: Limit price (None for market order)
            
        Returns:
            Order object if successful
        """
        order_type = OrderType.LIMIT if price is not None else OrderType.MARKET
        
        order = Order(
            symbol=symbol,
            side=OrderSide.BUY,
            quantity=quantity,
            order_type=order_type,
            price=price
        )
        
        if self.place_order(order):
            return order
        return None
    
    def sell(self, symbol: str, quantity: float, price: Optional[float] = None) -> Optional[Order]:
        """
        Place a sell order.
        
        Args:
            symbol: Trading symbol
            quantity: Quantity to sell
            price: Limit price (None for market order)
            
        Returns:
            Order object if successful
        """
        order_type = OrderType.LIMIT if price is not None else OrderType.MARKET
        
        order = Order(
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=quantity,
            order_type=order_type,
            price=price
        )
        
        if self.place_order(order):
            return order
        return None
    
    def cancel_all_orders(self, symbol: Optional[str] = None) -> bool:
        """
        Cancel all active orders for a symbol or all symbols.
        
        Args:
            symbol: Symbol to cancel orders for (None for all symbols)
            
        Returns:
            True if all orders were cancelled successfully
        """
        orders_to_cancel = []
        
        for order_id, order in self.active_orders.items():
            if symbol is None or order.symbol == symbol:
                orders_to_cancel.append(order_id)
        
        success = True
        for order_id in orders_to_cancel:
            if not self.cancel_order(order_id):
                success = False
        
        return success
    
    def update_all_orders(self) -> None:
        """Update status of all active orders."""
        for order_id in list(self.active_orders.keys()):
            self.get_order_status(order_id)
            
            # Move completed orders to history
            order = self.active_orders.get(order_id)
            if order and order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                del self.active_orders[order_id]
                self.order_history.append(order)
    
    def get_order_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Order]:
        """
        Get order history.
        
        Args:
            symbol: Filter by symbol (None for all symbols)
            limit: Maximum number of orders to return
            
        Returns:
            List of historical orders
        """
        history = self.order_history
        
        if symbol:
            history = [order for order in history if order.symbol == symbol]
        
        return history[-limit:]
    
    def get_active_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """
        Get active orders.
        
        Args:
            symbol: Filter by symbol (None for all symbols)
            
        Returns:
            List of active orders
        """
        orders = list(self.active_orders.values())
        
        if symbol:
            orders = [order for order in orders if order.symbol == symbol]
        
        return orders