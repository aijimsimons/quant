"""Simulated Polymarket data for paper trading."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import random


def generate_polymarket_price_data(
    market_id: str = "BTC-01012024",
    n_days: int = 30,
    start_price: float = 100.0,
    volatility: float = 0.5,  # Polymarket markets are more volatile
    drift: float = 0.0,
    interval_minutes: int = 5,
) -> pd.DataFrame:
    """
    Generate simulated Polymarket-style price data.
    
    Polymarket markets have:
    - Higher volatility than regular crypto
    - Binary outcomes (0-100 range for binary markets)
    - Mean-reverting behavior near election dates
    
    Args:
        market_id: Market identifier
        n_days: Number of days of data
        start_price: Starting price (0-100 for binary, $ for crypto)
        volatility: Price volatility (0.1 = 10% daily movement)
        drift: Price drift (positive = uptrend, negative = downtrend)
        interval_minutes: Data interval (5, 15, 60)
        
    Returns:
        DataFrame with timestamp, open, high, low, close, volume
    """
    np.random.seed(42)
    
    n_periods = n_days * (24 * 60 // interval_minutes)
    
    # Generate price path
    prices = np.zeros(n_periods)
    prices[0] = start_price
    
    # Mean reversion factor (Polymarket prices tend to revert)
    mean_reversion_speed = 0.05
    target_price = start_price
    
    for t in range(1, n_periods):
        # Random walk with volatility
        shock = np.random.normal(0, volatility)
        
        # Mean reversion toward target
        mr = mean_reversion_speed * (target_price - prices[t-1])
        
        # Drift
        d = drift
        
        # Combined movement
        prices[t] = prices[t-1] + shock + mr + d
        
        # Clamp prices (Polymarket binary markets are 0-100)
        if "binary" in market_id.lower() or "yes" in market_id.lower():
            prices[t] = max(0, min(100, prices[t]))
        else:
            # Crypto markets
            prices[t] = max(1, prices[t])
    
    # Generate OHLC from close prices
    opens = np.zeros(n_periods)
    highs = np.zeros(n_periods)
    lows = np.zeros(n_periods)
    closes = np.zeros(n_periods)
    volumes = np.zeros(n_periods)
    
    for t in range(n_periods):
        close = prices[t]
        open_price = prices[t-1] if t > 0 else start_price
        
        if t == 0:
            opens[t] = start_price
            highs[t] = start_price * 1.001
            lows[t] = start_price * 0.999
            closes[t] = start_price * 1.0005
            volumes[t] = 1000
        else:
            change = close - open_price
            
            if change >= 0:
                opens[t] = open_price
                closes[t] = close
                highs[t] = max(open_price, close) * (1 + np.random.uniform(0, 0.0005))
                lows[t] = min(open_price, close) * (1 - np.random.uniform(0, 0.0005))
            else:
                opens[t] = open_price
                closes[t] = close
                highs[t] = max(open_price, close) * (1 + np.random.uniform(0, 0.0005))
                lows[t] = min(open_price, close) * (1 - np.random.uniform(0, 0.0005))
            
            # Volume based on price movement
            volumes[t] = int(1000 + abs(change) * 1000)
    
    # Create timestamps
    start_time = datetime.now() - timedelta(days=n_days)
    timestamps = pd.date_range(
        start=start_time,
        periods=n_periods,
        freq=f'{interval_minutes}min'
    )
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes.astype(int),
    })
    
    return df


class SimulatedPolymarketClient:
    """
    Simulates Polymarket API for paper trading.
    
    Provides realistic Polymarket-style data without real API calls.
    """
    
    def __init__(
        self,
        initial_balance: float = 10000.0,
        testnet: bool = True,
    ):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.testnet = testnet
        self.markets: Dict[str, pd.DataFrame] = {}
        self.orders: List[dict] = []
        self.trades: List[dict] = []
        self.positions: Dict[str, float] = {}
    
    def load_market(
        self,
        market_id: str,
        n_days: int = 30,
        start_price: float = 100.0,
        volatility: float = 0.5,
    ) -> pd.DataFrame:
        """Load simulated market data."""
        data = generate_polymarket_price_data(
            market_id=market_id,
            n_days=n_days,
            start_price=start_price,
            volatility=volatility,
        )
        self.markets[market_id] = data
        return data
    
    def get_market(self, market_id: str) -> Optional[dict]:
        """Get market info."""
        if market_id not in self.markets:
            return None
        data = self.markets[market_id]
        return {
            "id": market_id,
            "price": data["close"].iloc[-1],
            "volume": data["volume"].sum(),
            "high": data["close"].max(),
            "low": data["close"].min(),
        }
    
    def get_prices(
        self,
        market_id: str,
        period: str = "24h",
        interval: str = "5m",
    ) -> pd.DataFrame:
        """Get price history for a market."""
        if market_id not in self.markets:
            # Load default data
            self.load_market(market_id)
        
        data = self.markets[market_id]
        
        # Filter by period (simple implementation)
        if period == "24h":
            cutoff = data["timestamp"].max() - pd.Timedelta(hours=24)
            data = data[data["timestamp"] >= cutoff]
        elif period == "7d":
            cutoff = data["timestamp"].max() - pd.Timedelta(days=7)
            data = data[data["timestamp"] >= cutoff]
        
        return data
    
    def place_order(
        self,
        market_id: str,
        side: str,
        price: float,
        size: float,
    ) -> dict:
        """Place a simulated order."""
        order = {
            "id": f"order_{len(self.orders)}",
            "marketId": market_id,
            "side": side,
            "price": price,
            "size": size,
            "status": "pending",
            "timestamp": datetime.now(),
        }
        self.orders.append(order)
        return order
    
    def fill_order(
        self,
        order: dict,
        fill_price: Optional[float] = None,
    ) -> dict:
        """Simulate order fill."""
        if fill_price is None:
            # Use current market price
            market_id = order["marketId"]
            if market_id in self.markets:
                fill_price = self.markets[market_id]["close"].iloc[-1]
            else:
                fill_price = order["price"]
        
        order["status"] = "filled"
        order["fillPrice"] = fill_price
        
        # Update position
        market_id = order["marketId"]
        if market_id not in self.positions:
            self.positions[market_id] = 0
        
        if order["side"] == "buy":
            self.positions[market_id] += order["size"]
        else:
            self.positions[market_id] -= order["size"]
        
        # Record trade
        self.trades.append({
            **order,
            "fillPrice": fill_price,
        })
        
        return order
    
    def get_position(self, market_id: str) -> float:
        """Get current position."""
        return self.positions.get(market_id, 0)
    
    def get_positions(self) -> Dict[str, float]:
        """Get all positions."""
        return self.positions.copy()
    
    def get_unrealized_pnl(self) -> Dict[str, float]:
        """Calculate unrealized P&L."""
        pnl = {}
        for market_id, position in self.positions.items():
            if position != 0:
                # Get current price
                if market_id in self.markets:
                    current_price = self.markets[market_id]["close"].iloc[-1]
                    # Calculate avg entry from trades
                    market_trades = [
                        t for t in self.trades 
                        if t["marketId"] == market_id
                    ]
                    if market_trades:
                        avg_entry = sum(
                            t["size"] * t["fillPrice"] 
                            for t in market_trades
                        ) / sum(t["size"] for t in market_trades)
                        pnl[market_id] = (current_price - avg_entry) * position
        return pnl
    
    def get_final_pnl(self) -> float:
        """Get final P&L."""
        return self.balance - self.initial_balance
    
    def reset(self):
        """Reset paper trading state."""
        self.balance = self.initial_balance
        self.positions.clear()
        self.orders.clear()
        self.trades.clear()
