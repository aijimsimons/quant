from quant.infrastructure.data.real_data import load_bitcoin_ohlcv_csv
from quant.strategies.mean_reversion_bitcoin import mean_reversion_bitcoin, calculate_metrics
import polars as pl

btc_df = load_bitcoin_ohlcv_csv()
data_polars = pl.from_pandas(btc_df)

# Run with default params
results = mean_reversion_bitcoin(data_polars, capital=10000.0, verbose=False)
print('Full results:')
print(results)

metrics = calculate_metrics(results, capital=10000.0)
print('\nMetrics:')
for k, v in metrics.items():
    print(f'  {k}: {v}')
