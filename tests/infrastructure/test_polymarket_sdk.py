"""Test if mean reversion works on 5-minute Bitcoin predictions."""

import sys
sys.path.insert(0, '/Users/xingjianliu/jim/quant')

from quant.strategies.mean_reversion import mean_reversion_strategy, calculate_metrics
from quant.infrastructure.data.generator import generate_minute_bars
import polars as pl

# Generate 5-minute data for 30 days
data_pd = generate_minute_bars(n_days=30, minutes_per_day=288)  # 288 = 24*60/5
data = pl.from_pandas(data_pd).lazy()

print(f"Generating {len(data_pd)} rows of 5-minute data...")
print(f"Date range: {data_pd['timestamp'].min()} to {data_pd['timestamp'].max()}")

# Adjust parameters for 5-minute bars
results = mean_reversion_strategy(
    data, 
    capital=10000.0,
    window=20,  # 20 five-minute bars = 100 minutes
    std_multiplier=2.0,
    position_size_pct=0.05,
    stop_loss_pct=0.015,
    take_profit_pct=0.025,
    max_holding_period=20,  # 20 five-minute bars = 100 minutes
)

# Handle both LazyFrame and DataFrame
if isinstance(results, pl.LazyFrame):
    results_df = results.collect()
else:
    results_df = results

metrics = calculate_metrics(results_df, capital=10000.0)

print(f"\nPerformance Metrics (30 days, 5-min bars):")
print(f"  Total Return: {metrics['total_return']*100:.2f}%")
print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"  Max Drawdown: {metrics['max_drawdown']*100:.2f}%")
print(f"  Win Rate: {metrics['win_rate']*100:.2f}%")
print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
print(f"  Total Trades: {metrics['total_trades']}")
print(f"  Avg Win: ${metrics['avg_win']:.2f}")
print(f"  Avg Loss: ${metrics['avg_loss']:.2f}")
print(f"  Final Equity: ${metrics['total_return']*10000 + 10000:,.2f}")
