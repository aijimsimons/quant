from quant.infrastructure.data.real_data import load_bitcoin_ohlcv_csv
from quant.strategies.mean_reversion_bitcoin import mean_reversion_bitcoin, calculate_metrics
import polars as pl

btc_df = load_bitcoin_ohlcv_csv()
data_polars = pl.from_pandas(btc_df)

# Run with aggressive params (very short window, very tight z-scores)
results = mean_reversion_bitcoin(
    data_polars,
    capital=10000.0,
    window=5,  # Very short window
    std_multiplier=1.0,  # Very tight bands
    min_zscore=-0.8,  # Very aggressive entry
    max_zscore=0.8,
    stop_loss_pct=0.01,  # 1% stop loss
    take_profit_pct=0.02,  # 2% take profit
    max_holding_period=15,  # Max 15 days
    verbose=False
)

metrics = calculate_metrics(results, capital=10000.0)
print("Aggressive parameters:")
for k, v in metrics.items():
    print(f"  {k}: {v}")

# Try even more aggressive
results2 = mean_reversion_bitcoin(
    data_polars,
    capital=10000.0,
    window=3,
    std_multiplier=0.8,
    min_zscore=-0.5,
    max_zscore=0.5,
    stop_loss_pct=0.005,
    take_profit_pct=0.01,
    max_holding_period=10,
    verbose=False
)

metrics2 = calculate_metrics(results2, capital=10000.0)
print("\nVery aggressive parameters:")
for k, v in metrics2.items():
    print(f"  {k}: {v}")
