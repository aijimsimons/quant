"""Quick test of mean reversion strategy."""

import sys
sys.path.insert(0, '/Users/xingjianliu/jim/quant')

from strategies.mean_reversion import mean_reversion_strategy, calculate_metrics
from infrastructure.data.generator import generate_minute_bars
import polars as pl

print("Import test passed!")

# Generate data and convert to polars
data_pd = generate_minute_bars(n_days=5)
data = pl.from_pandas(data_pd).lazy()

print(f"Generated {len(data_pd)} rows of data")

results = mean_reversion_strategy(data, capital=10000.0)
results_df = results.collect()

metrics = calculate_metrics(results_df, capital=10000.0)

print(f"\nPerformance Metrics:")
print(f"  Total Return: {metrics['total_return']*100:.2f}%")
print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"  Max Drawdown: {metrics['max_drawdown']*100:.2f}%")
print(f"  Win Rate: {metrics['win_rate']*100:.2f}%")
print(f"  Total Trades: {metrics['total_trades']}")
print(f"  Final Equity: ${metrics['total_return']*10000 + 10000:,.2f}")
