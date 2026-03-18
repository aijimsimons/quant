"""Test Simulated Polymarket paper trading."""

import sys
import os

os.chdir('/Users/xingjianliu/jim/quant')

# Import directly
from infrastructure.simulation import SimulatedPolymarketClient
from strategies.mean_reversion import mean_reversion_strategy, calculate_metrics
import polars as pl

# Initialize simulated Polymarket client
client = SimulatedPolymarketClient(initial_balance=10000.0)

print("=" * 60)
print("Simulated Polymarket Paper Trading")
print("=" * 60)

# Load simulated market data
print("\n1. Loading simulated BTC binary market data...")
market_data_pd = client.load_market(
    market_id="BTC-01012024",
    n_days=30,
    start_price=100.0,  # Binary market (0-100)
    volatility=0.5,  # High volatility
)
print(f"   Loaded {len(market_data_pd)} data points")
print(f"   Price range: ${market_data_pd['close'].min():.2f} - ${market_data_pd['close'].max():.2f}")

# Convert to polars
market_data = pl.from_pandas(market_data_pd)

# Run mean reversion strategy
print("\n2. Running mean reversion strategy...")
results = mean_reversion_strategy(
    market_data,
    capital=10000.0,
    window=20,
    std_multiplier=2.0,
    position_size_pct=0.05,
    stop_loss_pct=0.015,
    take_profit_pct=0.025,
    max_holding_period=60,
)

# results is already a DataFrame, no need to collect
if isinstance(results, pl.LazyFrame):
    results_df = results.collect()
else:
    results_df = results

metrics = calculate_metrics(results_df, capital=10000.0)

print("\n3. Performance Metrics:")
print(f"   Total Return: {metrics['total_return']*100:.2f}%")
print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"   Max Drawdown: {metrics['max_drawdown']*100:.2f}%")
print(f"   Win Rate: {metrics['win_rate']*100:.2f}%")
print(f"   Profit Factor: {metrics['profit_factor']:.2f}")
print(f"   Total Trades: {metrics['total_trades']}")
print(f"   Avg Win: ${metrics['avg_win']:.2f}")
print(f"   Avg Loss: ${metrics['avg_loss']:.2f}")
print(f"   Final Equity: ${metrics['total_return']*10000 + 10000:,.2f}")

print("\n4. Positions:")
for market, position in client.get_positions().items():
    print(f"   {market}: {position:.2f}")

print("\n5. Paper Trading Complete!")
print(f"   Initial Balance: ${client.initial_balance:,.2f}")
print(f"   Final Balance: ${client.balance:,.2f}")
print(f"   Total P&L: ${client.get_final_pnl():,.2f}")
