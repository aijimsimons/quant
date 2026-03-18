#!/usr/bin/env python3
"""Test the data splitter with real 1-minute Bitcoin data."""

import sys
sys.path.insert(0, '/Users/xingjianliu/jim/quant')

import pandas as pd
from quant.infrastructure.data import (
    create_train_validation_pipeline,
    train_validation_split,
)

# Load the 1-minute data
data = pd.read_csv('/Users/xingjianliu/jim/quant/data/btc_1min_2022_2026.csv')
data['timestamp'] = pd.to_datetime(data['timestamp'])

print("=" * 60)
print("  TESTING DATA SPLITTER WITH REAL 1-MINUTE BTC DATA")
print("=" * 60)
print(f"\nTotal data: {len(data):,} rows")
print(f"Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")

# Test 1: Create train/validation split with 80/20 ratio
print("\n--- Test 1: 80/20 Train/Validation Split ---")
result = create_train_validation_pipeline(data, train_ratio=0.8, verbose=True)

# Verify chronological split
train_end = pd.to_datetime(result['train_end'])
val_start = pd.to_datetime(result['val_start'])
assert train_end < val_start, "Chronological split failed!"
print("\n✅ Chronological split verified!")

# Test 2: Test with different ratios
print("\n--- Test 2: 70/30 Split ---")
result_70 = create_train_validation_pipeline(data, train_ratio=0.7, verbose=True)
assert result_70['train_size'] + result_70['val_size'] == len(data)
print("✅ Split sizes sum correctly!")

# Test 3: Direct function usage
print("\n--- Test 3: Direct train_validation_split() ---")
train_df, val_df = train_validation_split(data, train_ratio=0.85)
print(f"Train: {len(train_df):,} rows")
print(f"Val: {len(val_df):,} rows")
assert len(train_df) + len(val_df) == len(data)
print("✅ Direct function works!")

# Test 4: Verify no data leakage
print("\n--- Test 4: No Data Leakage Check ---")
train_timestamps = set(pd.to_datetime(result['train']['timestamp']))
val_timestamps = set(pd.to_datetime(result['val']['timestamp']))
overlap = train_timestamps & val_timestamps
assert len(overlap) == 0, f"Data leakage detected! {len(overlap)} overlapping timestamps"
print("✅ No timestamp overlap between train and validation!")

print("\n" + "=" * 60)
print("  ALL TESTS PASSED!")
print("=" * 60)
print("\nThe data splitter is ready for use in backtesting pipelines.")
print("\nExample usage:")
print("""
from quant.infrastructure.data import create_train_validation_pipeline

data = pd.read_csv('btc_1min.csv')
result = create_train_validation_pipeline(data, train_ratio=0.8)

train_df = result['train']
val_df = result['val']

# Use train_df for hyperparameter tuning
# Use val_df for single validation run (no further tuning)
""")
