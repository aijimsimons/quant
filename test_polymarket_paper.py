"""Test Polymarket paper trading pipeline."""

import sys
import os

# Change to the quant directory
os.chdir('/Users/xingjianliu/jim/quant')
sys.path.insert(0, '/Users/xingjianliu/jim/quant')

# Import directly
from infrastructure.polymarket import PaperPolymarketClient

# Initialize paper client
client = PaperPolymarketClient(initial_balance=10000.0)

print("Polymarket Paper Trading Client Initialized")
print(f"Initial Balance: ${client.initial_balance:,.2f}")

# Simulate some trades
print("\nSimulating trades...")

# Simulate BTC price movements
prices = [100.0, 101.0, 102.0, 101.5, 100.5, 99.5, 98.5, 99.0, 100.0, 101.0]

for i, price in enumerate(prices):
    if i == 0:
        # Buy at first price
        order = client.place_order(
            market_id="BTC-01012024",
            side="buy",
            price=price,
            size=10.0,
        )
    elif i == 5:
        # Sell at fifth price
        order = client.place_order(
            market_id="BTC-01012024",
            side="sell",
            price=price,
            size=10.0,
        )

# Fill orders
for order in client.orders:
    if order["side"] == "buy":
        client.fill_order(order, fill_price=order["price"])
    else:
        client.fill_order(order, fill_price=order["price"])

print(f"\nTrades executed: {len(client.trades)}")
print(f"Final Position: {client.get_position('BTC-01012024')}")
print(f"Final P&L: ${client.get_final_pnl():,.2f}")
print(f"Final Equity: ${client.balance:,.2f}")
