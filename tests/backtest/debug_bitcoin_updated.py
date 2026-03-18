from quant.infrastructure.data.real_data import load_bitcoin_ohlcv_csv
from quant.strategies.mean_reversion_bitcoin import mean_reversion_bitcoin, calculate_metrics
import polars as pl

btc_df = load_bitcoin_ohlcv_csv()
data_polars = pl.from_pandas(btc_df)

# Run with updated params (shorter window, tighter z-scores)
results = mean_reversion_bitcoin(
    data_polars,
    capital=10000.0,
    window=10,  # Shorter window
    std_multiplier=1.5,  # Tighter bands
    min_zscore=-1.0,  # More aggressive entry
    max_zscore=1.0,
    verbose=True
)

print("\n=== PnL Statistics ===")
pnl_series = results['pnl'].to_numpy()
nonzero_pnl = pnl_series[pnl_series != 0]
print(f"Non-zero PnL entries: {len(nonzero_pnl)}")
print(f"Non-zero PnL values: {nonzero_pnl}")

metrics = calculate_metrics(results, capital=10000.0)
print("\nMetrics:")
for k, v in metrics.items():
    print(f"  {k}: {v}")
