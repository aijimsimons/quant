"""Run a proper backtest on mean reversion strategy."""

from quant.strategies.mean_reversion import mean_reversion_strategy, calculate_metrics
from quant.infrastructure.data.generator import generate_minute_bars
import polars as pl

# Generate 30 days of data
data_pd = generate_minute_bars(n_days=30)
data = pl.from_pandas(data_pd)

print(f"Generating {len(data_pd)} rows of 30-day minute data...")
print(f"Date range: {data_pd['timestamp'].min()} to {data_pd['timestamp'].max()}")

results = mean_reversion_strategy(data, capital=10000.0)

# Handle both LazyFrame and DataFrame
if isinstance(results, pl.LazyFrame):
    results_df = results.collect()
else:
    results_df = results

metrics = calculate_metrics(results_df, capital=10000.0)

print(f"\nPerformance Metrics (30 days):")
print(f"  Total Return: {metrics['total_return']*100:.2f}%")
print(f"  Annualized Return: {(1 + metrics['total_return'])**(365/30) - 1:.2%}")
print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"  Max Drawdown: {metrics['max_drawdown']*100:.2f}%")
print(f"  Win Rate: {metrics['win_rate']*100:.2f}%")
print(f"  Total Trades: {metrics['total_trades']}")
print(f"  Final Equity: ${metrics['total_return']*10000 + 10000:,.2f}")
