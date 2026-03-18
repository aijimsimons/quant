"""Paper trading engine for strategy testing."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Literal, Optional

import pandas as pd


@dataclass
class PaperOrder:
    """Simulated order for paper trading."""

    id: str
    market_id: str
    side: Literal["long", "short"]
    size: float
    price: float
    timestamp: datetime
    status: Literal["pending", "filled", "cancelled"] = "pending"


class PaperTradingEngine:
    """
    Paper trading engine - simulates trading without real money.

    Use with real Polymarket data to test strategies before going live.
    """

    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions: Dict[str, float] = {}  # market_id -> position
        self.orders: List[PaperOrder] = []
        self.trades: List[dict] = []
        self.equity_history: List[dict] = []

    def place_order(
        self,
        market_id: str,
        side: Literal["long", "short"],
        size: float,
        price: float,
        timestamp: Optional[datetime] = None,
    ) -> PaperOrder:
        """Place a simulated order (no real execution)."""
        from uuid import uuid4

        order = PaperOrder(
            id=str(uuid4()),
            market_id=market_id,
            side=side,
            size=size,
            price=price,
            timestamp=timestamp or datetime.now(),
        )

        self.orders.append(order)
        return order

    def fill_order(
        self, order: PaperOrder, fill_price: float, timestamp: Optional[datetime] = None
    ):
        """Simulate order fill."""
        order.status = "filled"

        # Update position
        if order.market_id not in self.positions:
            self.positions[order.market_id] = 0

        if order.side == "long":
            self.positions[order.market_id] += order.size
        else:
            self.positions[order.market_id] -= order.size

        # Record trade
        self.trades.append(
            {
                "order_id": order.id,
                "market_id": order.market_id,
                "side": order.side,
                "size": order.size,
                "price": fill_price,
                "timestamp": timestamp or datetime.now(),
            }
        )

        # Update equity
        self._update_equity_history(timestamp)

    def cancel_order(self, order_id: str) -> bool:
        """Cancel a simulated order."""
        for order in self.orders:
            if order.id == order_id:
                order.status = "cancelled"
                return True
        return False

    def get_position(self, market_id: str) -> float:
        """Get current simulated position."""
        return self.positions.get(market_id, 0)

    def get_positions(self) -> Dict[str, float]:
        """Get all simulated positions."""
        return self.positions.copy()

    def get_unrealized_pnl(self, prices: Dict[str, float]) -> Dict[str, float]:
        """Calculate unrealized P&L for all positions."""
        pnl = {}
        for market_id, position in self.positions.items():
            if position != 0 and market_id in prices:
                # Get average entry price
                market_trades = [t for t in self.trades if t["market_id"] == market_id]
                if market_trades:
                    avg_entry = sum(t["size"] * t["price"] for t in market_trades) / sum(
                        t["size"] for t in market_trades
                    )
                    pnl[market_id] = (prices[market_id] - avg_entry) * position
        return pnl

    def _update_equity_history(self, timestamp: Optional[datetime] = None):
        """Update equity history."""
        unrealized_pnl = self.get_unrealized_pnl({})
        total_pnl = sum(unrealized_pnl.values())

        self.equity_history.append(
            {
                "timestamp": timestamp or datetime.now(),
                "balance": self.balance,
                "unrealized_pnl": total_pnl,
                "total_equity": self.balance + total_pnl,
            }
        )

    def get_final_pnl(self) -> float:
        """Get final P&L."""
        return self.balance - self.initial_balance

    def get_metrics(self) -> dict:
        """Get paper trading metrics."""
        if not self.equity_history:
            return {}

        pd.Series([e["total_equity"] for e in self.equity_history])

        return {
            "initial_balance": self.initial_balance,
            "final_balance": self.balance,
            "total_pnl": self.balance - self.initial_balance,
            "total_return": (self.balance - self.initial_balance) / self.initial_balance,
            "trades_count": len(self.trades),
            "positions": self.positions.copy(),
        }

    def reset(self):
        """Reset paper trading state."""
        self.balance = self.initial_balance
        self.positions.clear()
        self.orders.clear()
        self.trades.clear()
        self.equity_history.clear()
