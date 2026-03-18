#!/usr/bin/env python3
import pandas as pd

df = pd.read_csv('/Users/xingjianliu/jim/quant/data/btc_1min_2022_2026.csv')
print(f'Total rows: {len(df):,}')
print(f'Date range: {df["timestamp"].min()} to {df["timestamp"].max()}')
print(f'Price range: ${df["low"].min():,.0f} - ${df["high"].max():,.0f}')
print(f'Mean price: ${df["close"].mean():,.0f}')
