from quant.infrastructure.data.real_data import load_bitcoin_ohlcv_csv
from quant.strategies.mean_reversion_bitcoin import mean_reversion_bitcoin
import polars as pl

btc_df = load_bitcoin_ohlcv_csv()
data_polars = pl.from_pandas(btc_df)

# Run with verbose to see actual PnL
results = mean_reversion_bitcoin(data_polars, capital=10000.0, verbose=True)

print("\n\n=== PnL Statistics ===")
pnl_series = results['pnl'].to_numpy()
nonzero_pnl = pnl_series[pnl_series != 0]
print(f"Non-zero PnL entries: {len(nonzero_pnl)}")
print(f"Non-zero PnL values: {nonzero_pnl}")
