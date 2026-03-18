"""Polymarket integration for paper trading."""

from typing import Dict, List, Optional, Literal
from datetime import datetime
import requests


class PolymarketClient:
    """
    Client for Polymarket API.
    
    Supports both testnet and mainnet.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        secret: Optional[str] = None,
        testnet: bool = True,
    ):
        """
        Initialize Polymarket client.
        
        Args:
            api_key: API key (get from polymarket.com/dashboard/api-keys)
            secret: API secret
            testnet: Use testnet (true) or mainnet (false)
        """
        self.api_key = api_key
        self.secret = secret
        self.testnet = testnet
        
        if testnet:
            self.base_url = "https://testnet.polymarket.com"
        else:
            self.base_url = "https://polymarket.com"
        
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            })
    
    def get_markets(
        self,
        limit: int = 100,
        offset: int = 0,
        active: bool = True,
    ) -> List[dict]:
        """
        Get markets.
        
        Args:
            limit: Max results
            offset: Pagination offset
            active: Only active markets
            
        Returns:
            List of market data
        """
        params = {
            "limit": limit,
            "offset": offset,
            "active": str(active).lower(),
        }
        
        response = self.session.get(f"{self.base_url}/api/markets", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_market(self, market_id: str) -> dict:
        """
        Get a specific market.
        
        Args:
            market_id: Market ID
            
        Returns:
            Market data
        """
        response = self.session.get(f"{self.base_url}/api/markets/{market_id}")
        response.raise_for_status()
        return response.json()
    
    def get_orderbook(self, market_id: str) -> dict:
        """
        Get orderbook for a market.
        
        Args:
            market_id: Market ID
            
        Returns:
            Orderbook data
        """
        response = self.session.get(f"{self.base_url}/api/orderbook/{market_id}")
        response.raise_for_status()
        return response.json()
    
    def get_prices(
        self,
        market_id: str,
        period: str = "1h",
        interval: str = "1m",
    ) -> List[dict]:
        """
        Get price history.
        
        Args:
            market_id: Market ID
            period: Time period (1h, 24h, 7d, 30d)
            interval: Candle interval (1m, 5m, 15m, 1h)
            
        Returns:
            List of price data
        """
        params = {
            "period": period,
            "interval": interval,
        }
        
        response = self.session.get(
            f"{self.base_url}/api/price/{market_id}",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_positions(
        self,
        wallet_address: Optional[str] = None,
    ) -> List[dict]:
        """
        Get user positions.
        
        Args:
            wallet_address: Wallet address (default: use auth)
            
        Returns:
            List of positions
        """
        if wallet_address:
            url = f"{self.base_url}/api/positions/{wallet_address}"
        else:
            url = f"{self.base_url}/api/positions"
        
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def place_order(
        self,
        market_id: str,
        side: Literal["buy", "sell"],
        price: float,
        size: float,
    ) -> dict:
        """
        Place an order.
        
        Args:
            market_id: Market ID
            side: "buy" or "sell"
            price: Order price
            size: Order size
            
        Returns:
            Order response
        """
        payload = {
            "marketId": market_id,
            "side": side,
            "price": price,
            "size": size,
        }
        
        response = self.session.post(
            f"{self.base_url}/api/order",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def cancel_order(self, order_id: str) -> dict:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID
            
        Returns:
            Cancel response
        """
        response = self.session.delete(
            f"{self.base_url}/api/order/{order_id}"
        )
        response.raise_for_status()
        return response.json()


class PaperPolymarketClient(PolymarketClient):
    """
    Paper trading client for Polymarket.
    
    Simulates trading without real money.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        secret: Optional[str] = None,
        testnet: bool = True,
        initial_balance: float = 10000.0,
    ):
        super().__init__(api_key, secret, testnet)
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions: Dict[str, float] = {}
        self.orders: List[dict] = []
        self.trades: List[dict] = []
    
    def place_order(
        self,
        market_id: str,
        side: Literal["buy", "sell"],
        price: float,
        size: float,
    ) -> dict:
        """Simulate order placement (no real execution)."""
        order = {
            "id": f"paper_{len(self.orders)}",
            "marketId": market_id,
            "side": side,
            "price": price,
            "size": size,
            "status": "pending",
            "timestamp": datetime.now().isoformat(),
        }
        
        self.orders.append(order)
        return order
    
    def fill_order(self, order: dict, fill_price: float):
        """Simulate order fill."""
        order["status"] = "filled"
        order["fillPrice"] = fill_price
        
        # Update position
        if order["marketId"] not in self.positions:
            self.positions[order["marketId"]] = 0
        
        if order["side"] == "buy":
            self.positions[order["marketId"]] += order["size"]
        else:
            self.positions[order["marketId"]] -= order["size"]
        
        # Record trade
        self.trades.append({
            **order,
            "fillPrice": fill_price,
            "timestamp": datetime.now().isoformat(),
        })
        
        return order
    
    def get_position(self, market_id: str) -> float:
        """Get current position."""
        return self.positions.get(market_id, 0)
    
    def get_positions(self) -> Dict[str, float]:
        """Get all positions."""
        return self.positions.copy()
    
    def get_unrealized_pnl(self, prices: Dict[str, float]) -> Dict[str, float]:
        """Calculate unrealized P&L."""
        pnl = {}
        for market_id, position in self.positions.items():
            if position != 0 and market_id in prices:
                # Calculate avg entry price from trades
                market_trades = [
                    t for t in self.trades 
                    if t["marketId"] == market_id
                ]
                if market_trades:
                    avg_entry = sum(
                        t["size"] * t["fillPrice"] 
                        for t in market_trades
                    ) / sum(t["size"] for t in market_trades)
                    pnl[market_id] = (prices[market_id] - avg_entry) * position
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
