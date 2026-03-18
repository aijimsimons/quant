#!/usr/bin/env python3
"""Test imports and data splitter with 1-minute data."""

import sys
sys.path.insert(0, '/Users/xingjianliu/jim/quant')

from quant.infrastructure.data import (
    create_train_validation_pipeline,
    load_bitcoin_1min_csv,
    get_bitcoin_1min_data,
)

print('Imports successful!')

# Test 1-minute data loading
data = load_bitcoin_1min_csv()
print(f'Loaded {len(data):,} rows of 1-minute data')
print(f'Date range: {data["timestamp"].min()} to {data["timestamp"].max()}')

# Test splitter
result = create_train_validation_pipeline(data, train_ratio=0.8, verbose=False)
print(f'Train: {result["train_size"]:,}, Val: {result["val_size"]:,}')

print("\n✅ All imports and functions working!")
