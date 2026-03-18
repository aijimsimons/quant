"""Debug signal generation."""

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

# Generate signals
data = data.with_columns([
    pl.when(pl.col('zscore').shift(1) < -2.0).then(pl.lit(1))
    .when(pl.col('zscore').shift(1) > 2.0).then(pl.lit(-1))
    .otherwise(pl.lit(0)).alias('signal')
])

# Check signal counts
print('Signal counts:')
print(data.select([
    (pl.col('signal') == 1).sum().alias('long_signals'),
    (pl.col('signal') == -1).sum().alias('short_signals'),
    (pl.col('signal') == 0).sum().alias('no_signal'),
]))

# Show some signals
print('\nRows with signals:')
print(data.filter(pl.col('signal') != 0).select(['timestamp', 'close', 'zscore', 'signal']).head(10))
