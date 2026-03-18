"""Core data types for quant trading."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass
class Bar:
    """OHLCV bar data."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    
    @property
    def body(self) -> float:
        """Get bar body size."""
        return abs(self.close - self.open)
    
    @property
    def upper_wick(self) -> float:
        """Get upper wick size."""
        return self.high - max(self.open, self.close)
    
    @property
    def lower_wick(self) -> float:
        """Get lower wick size."""
        return min(self.open, self.close) - self.low
    
    @property
    def is_bullish(self) -> bool:
        """Check if bar is bullish."""
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        """Check if bar is bearish."""
        return self.close < self.open


@dataclass
class Trade:
    """Trade execution data."""
    timestamp: datetime
    symbol: str
    side: Literal["long", "short"]
    price: float
    size: float
    fee: float = 0.0
    
    @property
    def value(self) -> float:
        """Get trade value."""
        return self.price * self.size
    
    @property
    def pnl(self) -> float:
        """Get P&L (requires exit price)."""
        raise NotImplementedError("PnL requires exit price")


@dataclass
class Position:
    """Current position state."""
    symbol: str
    side: Literal["long", "short"]
    entry_price: float
    size: float
    entry_time: datetime
    unrealized_pnl: float = 0.0
    
    @property
    def value(self) -> float:
        """Get position value."""
        return self.entry_price * self.size
    
    def close(self, exit_price: float, exit_time: datetime) -> Trade:
        """Close position and return trade record."""
        return Trade(
            timestamp=exit_time,
            symbol=self.symbol,
            side="short" if self.side == "long" else "long",
            price=exit_price,
            size=self.size,
        )
