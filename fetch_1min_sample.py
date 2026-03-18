#!/usr/bin/env python3
"""Fetch sample 1-minute Bitcoin data to test the API."""

import ccxt
import pandas as pd
from datetime import datetime
import time
from pathlib import Path

# Initialize Coinbase exchange
exchange = ccxt.coinbase({
    'enableRateLimit': True,
    'options': {
        'adjustForTimeDifference': True,
    }
})

symbol = 'BTC/USD'
timeframe = '1m'

print("=" * 60)
print("  TESTING 1-MINUTE BITCOIN DATA FETCH")
print("=" * 60)

# Test with a small date range first
start_date = "2026-03-10"  # Just 8 days of data
end_date = "2026-03-18"  # To today

start_ms = int(pd.Timestamp(start_date).timestamp() * 1000)
end_ms = int(pd.Timestamp(end_date).timestamp() * 1000)

print(f"\nFetching from {start_date} to {end_date}...")
print(f"Total minutes: {(end_ms - start_ms) // 60000:,}")
print(f"Expected candles: ~{((end_ms - start_ms) // 60000):,}")

all_candles = []
current_start = start_ms

while current_start < end_ms:
    try:
        print(f"\nFetching from {pd.Timestamp(current_start, unit='ms')}...")
        
        candles = exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            since=current_start,
            limit=1000
        )
        
        if len(candles) == 0:
            print("  No more data")
            break
        
        all_candles.extend(candles)
        last_timestamp = candles[-1][0]
        current_start = last_timestamp + 60000  # Add 1 minute in ms
        
        print(f"  Got {len(candles)} candles, total so far: {len(all_candles):,}")
        
        # Rate limiting
        time.sleep(exchange.rateLimit / 1000)
        
    except Exception as e:
        print(f"  Error: {e}")
        print("  Waiting 30s...")
        time.sleep(30)
        continue

# Convert to DataFrame
df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

print(f"\n{'=' * 60}")
print(f"  FETCHED {len(df):,} CANDLES")
print(f"{'=' * 60}")
print(f"\nDate range: {df['timestamp'].min()} to {df['timestamp'].max()}")
print(f"Price range: ${df['low'].min():,.0f} - ${df['high'].max():,.0f}")
print(f"\nFirst few rows:")
print(df.head())
print(f"\nLast few rows:")
print(df.tail())

# Save to CSV
output_path = Path("/Users/xingjianliu/jim/quant/data/btc_1min_test.csv")
df.to_csv(output_path, index=False)
print(f"\nSaved to: {output_path}")
