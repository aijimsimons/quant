"""Test mean reversion strategy on Polymarket 5-minute binary data."""

from quant.strategies.mean_reversion_polymarket import mean_reversion_polymarket, calculate_metrics
from quant.infrastructure.simulation import generate_polymarket_price_data
import polars as pl

# Generate 30 days of 5-minute Polymarket data
print("Generating 30 days of 5-minute Polymarket binary market data...")
data_pd = generate_polymarket_price_data(
    market_id="BTC-01012024-binary",
    n_days=30,
    start_price=50.0,  # Binary market centered at 50
    volatility=0.8,    # Higher volatility for binary markets
    drift=0.0,
    interval_minutes=5,
)

data = pl.from_pandas(data_pd)

print(f"Generated {len(data_pd)} rows of data")
print(f"Date range: {data_pd['timestamp'].min()} to {data_pd['timestamp'].max()}")
print(f"Price range: ${data_pd['close'].min():.2f} - ${data_pd['close'].max():.2f}")
print(f"Price mean: ${data_pd['close'].mean():.2f} (target: 50.0)")

# Run polymarket-specific mean reversion strategy
results = mean_reversion_polymarket(
    data,
    capital=10000.0,
    window=20,           # 20 five-minute bars
    std_multiplier=1.5,  # Tighter bands for binary
    position_size_pct=0.05,
    stop_loss_pct=0.02,  # 2% stop loss
    take_profit_pct=0.03,  # 3% take profit
    max_holding_period=20,  # 100 minutes max hold
    min_zscore=-0.8,
    max_zscore=0.8,
    slippage_pct=0.001,
    verbose=False,
)

metrics = calculate_metrics(results, capital=10000.0)

print("\n" + "="*60)
print("Polymarket Mean Reversion Strategy Results (30 days, 5-min)")
print("="*60)
print(f"\nPerformance Metrics:")
print(f"  Total Return:     {metrics['total_return']*100:+.2f}%")
print(f"  Annualized Return: {(1 + metrics['total_return'])**(72576/len(results)) - 1:+.2f}%")
print(f"  Sharpe Ratio:     {metrics['sharpe_ratio']:.2f}")
print(f"  Max Drawdown:     {metrics['max_drawdown']*100:+.2f}%")
print(f"  Win Rate:         {metrics['win_rate']*100:.2f}%")
print(f"  Profit Factor:    {metrics['profit_factor']:.2f}")
print(f"  Total Trades:     {metrics['total_trades']}")
print(f"  Avg Win:          ${metrics['avg_win']:.2f}")
print(f"  Avg Loss:         ${metrics['avg_loss']:.2f}")
print(f"  Final Equity:     ${metrics['total_return']*10000 + 10000:,.2f}")

# Additional analysis
print("\n" + "="*60)
print("Position Analysis")
print("="*60)

position_stats = results.select([
    pl.col('position').abs().sum().alias('total_position_units'),
    pl.col('position').abs().mean().alias('avg_position_units'),
    (pl.col('position') != 0).sum().alias('bars_with_position'),
])

print(f"  Total position units traded: {position_stats['total_position_units'][0]:,.0f}")
print(f"  Avg position per trade: {position_stats['avg_position_units'][0]:.2f}")
print(f"  Bars with position: {position_stats['bars_with_position'][0]:.0f} / {len(results)}")

# Check for look-ahead bias
print("\n" + "="*60)
print("Look-Ahead Bias Check")
print("="*60)
zscore_check = results.filter(pl.col('zscore').abs() > 1.0).select([
    (pl.col('zscore') > 0).sum().alias('high_zscore'),
    (pl.col('zscore') < 0).sum().alias('low_zscore'),
])
print(f"  High zscore (>1.0) periods: {zscore_check['high_zscore'][0]}")
print(f"  Low zscore (<-1.0) periods: {zscore_check['low_zscore'][0]}")
