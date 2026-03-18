"""Risk management for quant strategies."""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd


@dataclass
class PositionLimit:
    """Position size limits."""
    symbol: str
    max_units: int = 100
    max_notional: float = 50000.0
    max_daily_trades: int = 100
    max_exposure_pct: float = 0.10


@dataclass
class RiskLimit:
    """Overall risk limits."""
    max_drawdown_pct: float = 0.15
    max_position_pct: float = 0.20
    max_leverage: float = 2.0
    max_daily_loss_pct: float = 0.10


class RiskManager:
    """Manages risk for trading strategies."""
    
    def __init__(
        self,
        capital: float = 10000.0,
        position_limits: Optional[List[PositionLimit]] = None,
        risk_limits: Optional[RiskLimit] = None
    ):
        self.capital = capital
        self.position_limits = position_limits or []
        self.risk_limits = risk_limits or RiskLimit()
        
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.positions: Dict[str, float] = {}
        self.start_of_day_equity = capital
    
    def check_position(
        self,
        symbol: str,
        size: int,
        price: float,
        side: str
    ) -> tuple[bool, str]:
        """Check if a position is allowed."""
        notional = abs(size * price)
        
        limit = self._get_limit(symbol)
        if limit:
            if abs(size) > limit.max_units:
                return False, f"Position exceeds max units ({limit.max_units})"
            if notional > limit.max_notional:
                return False, f"Notional exceeds max ({limit.max_notional})"
        
        position_pct = notional / self.capital
        if position_pct > self.risk_limits.max_position_pct:
            return False, f"Position exceeds max % ({self.risk_limits.max_position_pct*100:.0f}%)"
        
        total_exposure = sum(abs(p) for p in self.positions.values()) + notional
        if total_exposure / self.capital > self.risk_limits.max_leverage:
            return False, "Leverage exceeds maximum"
        
        return True, "OK"
    
    def check_drawdown(self, current_equity: float) -> tuple[bool, str]:
        """Check if drawdown exceeds limit."""
        peak = max(self.start_of_day_equity, current_equity)
        drawdown = (peak - current_equity) / peak if peak > 0 else 0
        
        if drawdown >= self.risk_limits.max_drawdown_pct:
            return False, f"Drawdown {drawdown*100:.2f}% exceeds limit"
        
        return True, "OK"
    
    def check_daily_loss(self, current_equity: float) -> tuple[bool, str]:
        """Check if daily loss exceeds limit."""
        daily_loss = self.start_of_day_equity - current_equity
        
        if daily_loss > self.capital * self.risk_limits.max_daily_loss_pct:
            return False, "Daily loss exceeds limit"
        
        return True, "OK"
    
    def record_trade(self, symbol: str, size: int, price: float, pnl: float):
        """Record a trade for tracking."""
        self.daily_trades += 1
        self.daily_pnl += pnl
        
        if symbol not in self.positions:
            self.positions[symbol] = 0
        self.positions[symbol] += size
    
    def reset_daily(self):
        """Reset daily counters."""
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.start_of_day_equity = self.capital
    
    def _get_limit(self, symbol: str) -> Optional[PositionLimit]:
        """Get position limit for symbol."""
        for limit in self.position_limits:
            if limit.symbol == symbol:
                return limit
        return None
