from quant.infrastructure.data.real_data import load_bitcoin_ohlcv_csv
from quant.strategies.mean_reversion_bitcoin import mean_reversion_bitcoin
import polars as pl

btc_df = load_bitcoin_ohlcv_csv()
data_polars = pl.from_pandas(btc_df)

# Run with default params
results = mean_reversion_bitcoin(data_polars, capital=10000.0, verbose=False)

# Show only rows where position changed
print("Trade entries (position != 0):")
for row in results.iter_rows(named=True):
    if row['position'] != 0:
        print(f"{row['timestamp']}: Position={row['position']:.4f}, Entry Price={row['entry_price']:.2f}, Close={row['close']:.2f}, PnL={row['pnl']:.2f}")
