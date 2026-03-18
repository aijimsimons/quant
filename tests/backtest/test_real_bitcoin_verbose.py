"""Test mean reversion on real Bitcoin data with verbose output."""

import sys
sys.path.insert(0, '/Users/xingjianliu/jim/quant')

from quant.infrastructure.data.real_data import load_bitcoin_ohlcv_csv
from quant.strategies.mean_reversion_bitcoin import mean_reversion_bitcoin, calculate_metrics
import polars as pl

btc_df = load_bitcoin_ohlcv_csv()
data = pl.from_pandas(btc_df)

# Run with verbose output
results = mean_reversion_bitcoin(
    data,
    capital=10000.0,
    window=20,
    std_multiplier=2.0,
    position_size_pct=0.05,
    stop_loss_pct=0.02,
    take_profit_pct=0.03,
    max_holding_period=20,
    min_zscore=-2.0,
    max_zscore=2.0,
    slippage_pct=0.001,
    verbose=True,
)

metrics = calculate_metrics(results, capital=10000.0)

print("\nPerformance Metrics:")
print(f"  Total Return: {metrics['total_return']*100:+.2f}%")
print(f"  Total Trades: {metrics['total_trades']}")
print(f"  Final Equity: ${metrics['total_return']*10000 + 10000:,.2f}")
