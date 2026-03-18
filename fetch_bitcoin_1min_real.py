#!/usr/bin/env python3
"""Fetch real Bitcoin 1-minute data from Coinbase Pro via CCXT."""

import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time
import os
from pathlib import Path

# Paths
DATA_DIR = Path("/Users/xingjianliu/jim/quant/data")
DATA_DIR.mkdir(exist_ok=True)

# Initialize Coinbase exchange (Coinbase Pro is now just Coinbase)
exchange = ccxt.coinbase({
    'enableRateLimit': True,
    'options': {
        'adjustForTimeDifference': True,
    }
})

def fetch_1min_bitcoin_data(years: list = None, start_date: str = None, end_date: str = None):
    """
    Fetch 1-minute Bitcoin OHLCV data from Coinbase Pro.
    
    Args:
        years: List of years to fetch (e.g., [2022, 2026])
        start_date: Start date in 'YYYY-MM-DD' format (optional)
        end_date: End date in 'YYYY-MM-DD' format (optional)
    
    Returns:
        DataFrame with timestamp, open, high, low, close, volume
    """
    if years is None and start_date is None:
        # Default: current year (2026) to now
        start_date = "2026-01-01"
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    all_data = []
    
    # Convert to timestamps
    if start_date:
        if isinstance(start_date, str):
            start_ms = int(pd.Timestamp(start_date).timestamp() * 1000)
        else:
            start_ms = int(start_date.timestamp() * 1000)
    else:
        # Default: 1 year ago
        start_ms = int((datetime.now() - timedelta(days=365)).timestamp() * 1000)
    
    if end_date:
        if isinstance(end_date, str):
            end_ms = int(pd.Timestamp(end_date).timestamp() * 1000)
        else:
            end_ms = int(end_date.timestamp() * 1000)
    else:
        end_ms = int(datetime.now().timestamp() * 1000)
    
    print(f"Fetching Bitcoin 1-minute data...")
    print(f"From: {pd.Timestamp(start_ms, unit='ms')}")
    print(f"To: {pd.Timestamp(end_ms, unit='ms')}")
    
    # Coinbase Pro has a 1000 candle limit per request
    # 1-minute candles: 1000 minutes = ~16.7 hours per request
    timeframe = '1m'
    symbol = 'BTC/USD'
    
    current_start = start_ms
    
    while current_start < end_ms:
        try:
            print(f"  Fetching from {pd.Timestamp(current_start, unit='ms')}...")
            
            candles = exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                since=current_start,
                limit=1000
            )
            
            if len(candles) == 0:
                print("  No more data available")
                break
            
            # Convert to DataFrame
            df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Add to all_data
            all_data.append(df)
            
            # Update start time for next iteration
            last_timestamp = df['timestamp'].iloc[-1]
            current_start = int((last_timestamp + timedelta(minutes=1)).timestamp() * 1000)
            
            # Rate limiting
            time.sleep(exchange.rateLimit / 1000)
            
            print(f"    Got {len(df)} candles, next start: {pd.Timestamp(current_start, unit='ms')}")
            
        except ccxt.NetworkError as e:
            print(f"  Network error: {e}")
            print(f"  Waiting 60s before retry...")
            time.sleep(60)
            continue
        except ccxt.ExchangeError as e:
            print(f"  Exchange error: {e}")
            break
    
    if not all_data:
        raise ValueError("No data fetched!")
    
    # Concatenate all data
    result = pd.concat(all_data, ignore_index=True)
    
    # Sort by timestamp
    result = result.sort_values('timestamp').reset_index(drop=True)
    
    # Remove duplicates
    result = result.drop_duplicates(subset=['timestamp'])
    
    return result


def save_data(df: pd.DataFrame, filename: str):
    """Save DataFrame to CSV."""
    filepath = DATA_DIR / filename
    df.to_csv(filepath, index=False)
    print(f"Data saved to: {filepath}")
    return filepath


def main():
    print("=" * 70)
    print("  FETCHING REAL BITCOIN 1-MINUTE DATA")
    print("=" * 70)
    
    # Fetch 2022 data
    print("\n--- Fetching 2022 data (Jan 1 - Dec 31, 2022) ---")
    try:
        data_2022 = fetch_1min_bitcoin_data(
            start_date="2022-01-01",
            end_date="2022-12-31"
        )
        save_data(data_2022, "btc_1min_2022.csv")
        print(f"2022 data: {len(data_2022)} rows")
        print(f"  Date range: {data_2022['timestamp'].min()} to {data_2022['timestamp'].max()}")
    except Exception as e:
        print(f"Error fetching 2022 data: {e}")
        data_2022 = None
    
    # Fetch 2026 data (to current date)
    print("\n--- Fetching 2026 data (Jan 1 - present) ---")
    try:
        data_2026 = fetch_1min_bitcoin_data(
            start_date="2026-01-01",
            end_date=datetime.now().strftime("%Y-%m-%d")
        )
        save_data(data_2026, "btc_1min_2026.csv")
        print(f"2026 data: {len(data_2026)} rows")
        print(f"  Date range: {data_2026['timestamp'].min()} to {data_2026['timestamp'].max()}")
    except Exception as e:
        print(f"Error fetching 2026 data: {e}")
        data_2026 = None
    
    # Combine data if both available
    if data_2022 is not None and data_2026 is not None:
        print("\n--- Combining all data ---")
        combined = pd.concat([data_2022, data_2026], ignore_index=True)
        combined = combined.sort_values('timestamp').reset_index(drop=True)
        save_data(combined, "btc_1min_2022_2026.csv")
        print(f"Combined data: {len(combined)} rows")
        print(f"  Date range: {combined['timestamp'].min()} to {combined['timestamp'].max()}")
    
    print("\n" + "=" * 70)
    print("  FETCH COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
