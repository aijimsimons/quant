"""Execution clients for trading strategies."""

from typing import Dict, List, Optional, Literal
from dataclasses import dataclass
from datetime import datetime
import pandas as pd


@dataclass
class Order:
    """Order to execute."""
    id: str
    symbol: str
    side: Literal["long", "short"]
    type: Literal["market", "limit", "stop", "stop_limit"]
    size: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    timestamp: Optional[datetime] = None
    status: Literal["pending", "open", "filled", "cancelled", "rejected"] = "pending"
    filled_size: float = 0.0
    filled_price: Optional[float] = None
    commission: float = 0.0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class Fill:
    """Order fill record."""
    order_id: str
    symbol: str
    side: Literal["long", "short"]
    size: float
    price: float
    timestamp: datetime
    commission: float = 0.0


class ExecutionClient:
    """Base execution client."""
    
    def __init__(self, initial_balance: float = 10000.0):
        self.balance = initial_balance
        self.orders: Dict[str, Order] = {}
        self.fills: List[Fill] = []
        self.positions: Dict[str, float] = {}
    
    def create_order(
        self,
        symbol: str,
        side: Literal["long", "short"],
        size: float,
        order_type: Literal["market", "limit", "stop", "stop_limit"] = "market",
        price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Order:
        """Create a new order."""
        from uuid import uuid4
        
        order = Order(
            id=str(uuid4()),
            symbol=symbol,
            side=side,
            type=order_type,
            size=size,
            price=price,
            stop_price=stop_price,
        )
        
        self.orders[order.id] = order
        return order
    
    def submit_order(self, order: Order) -> bool:
        """Submit an order for execution."""
        order.status = "pending"
        return True
    
    def fill_order(self, order: Order, fill_price: float, fill_size: Optional[float] = None):
        """Fill an order."""
        if fill_size is None:
            fill_size = order.size
        
        commission = fill_size * fill_price * 0.001
        
        self.balance -= commission
        
        if order.symbol not in self.positions:
            self.positions[order.symbol] = 0
        
        if order.side == "long":
            self.positions[order.symbol] += fill_size
        else:
            self.positions[order.symbol] -= fill_size
        
        fill = Fill(
            order_id=order.id,
            symbol=order.symbol,
            side=order.side,
            size=fill_size,
            price=fill_price,
            timestamp=datetime.now(),
            commission=commission,
        )
        self.fills.append(fill)
        
        order.status = "filled"
        order.filled_size = fill_size
        order.filled_price = fill_price
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        if order_id in self.orders:
            self.orders[order_id].status = "cancelled"
            return True
        return False
    
    def get_position(self, symbol: str) -> float:
        """Get current position for symbol."""
        return self.positions.get(symbol, 0)
    
    def get_positions(self) -> Dict[str, float]:
        """Get all positions."""
        return self.positions.copy()
    
    def get_unrealized_pnl(self, prices: Dict[str, float]) -> Dict[str, float]:
        """Calculate unrealized P&L for all positions."""
        pnl = {}
        for symbol, position in self.positions.items():
            if position != 0 and symbol in prices:
                entry_price = self._get_entry_price(symbol)
                pnl[symbol] = (prices[symbol] - entry_price) * position
        return pnl
    
    def _get_entry_price(self, symbol: str) -> float:
        """Get average entry price for symbol."""
        fills = [f for f in self.fills if f.symbol == symbol and f.side == "long"]
        if not fills:
            return 0.0
        
        total_value = sum(f.size * f.price for f in fills)
        total_size = sum(f.size for f in fills)
        return total_value / total_size if total_size > 0 else 0.0


class BacktestExecutionClient(ExecutionClient):
    """Execution client for backtesting."""
    
    def __init__(self, initial_balance: float = 10000.0, slippage: float = 0.0005):
        super().__init__(initial_balance)
        self.slippage = slippage
    
    def fill_order(self, order: Order, fill_price: float, fill_size: Optional[float] = None):
        """Fill with slippage for backtesting realism."""
        if order.side == "long":
            fill_price *= (1 + self.slippage)
        else:
            fill_price *= (1 - self.slippage)
        
        super().fill_order(order, fill_price, fill_size)
