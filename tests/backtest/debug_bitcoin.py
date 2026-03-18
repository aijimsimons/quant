"""Debug Bitcoin data for mean reversion."""

import sys
sys.path.insert(0, '/Users/xingjianliu/jim/quant')

from quant.infrastructure.data.real_data import load_bitcoin_ohlcv_csv
import polars as pl

btc_df = load_bitcoin_ohlcv_csv()
data = pl.from_pandas(btc_df)

# Calculate Bollinger Bands
data = data.with_columns([
    pl.col('close').rolling_mean(20).alias('sma'),
    pl.col('close').rolling_std(20).alias('std'),
])
data = data.with_columns([
    ((pl.col('close') - pl.col('sma')) / pl.col('std')).alias('zscore'),
])

# Check zscore values
print('Z-score statistics:')
zscore_data = data.select([
    pl.col('zscore').min().alias('min'),
    pl.col('zscore').max().alias('max'),
    pl.col('zscore').mean().alias('mean'),
    pl.col('zscore').std().alias('std'),
])
print(zscore_data)

# Check signal values
print('\nFirst 25 rows:')
print(data.select(['timestamp', 'close', 'sma', 'std', 'zscore']).head(25))
