#!/usr/bin/env python3
"""Fetch real Bitcoin 1-minute data from multiple exchanges for comprehensive coverage."""

import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time
from pathlib import Path

# Initialize exchanges
exchanges = {
    'coinbase': ccxt.coinbase({'enableRateLimit': True}),
    'binance': ccxt.binance({'enableRateLimit': True}),
}

DATA_DIR = Path("/Users/xingjianliu/jim/quant/data")
DATA_DIR.mkdir(exist_ok=True)

def fetch_from_exchange(exchange, symbol='BTC/USD', timeframe='1m', start_ms=None, end_ms=None, max_retries=3):
    """Fetch OHLCV data from an exchange with retry logic."""
    all_candles = []
    current_start = start_ms
    attempts = 0
    
    while current_start < end_ms and attempts < max_retries:
        try:
            candles = exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                since=current_start,
                limit=1000
            )
            
            if len(candles) == 0:
                print("    No more data available")
                break
            
            all_candles.extend(candles)
            last_timestamp = candles[-1][0]
            current_start = last_timestamp + 60000  # Add 1 minute
            
            attempts = 0  # Reset retry counter on success
            time.sleep(exchange.rateLimit / 1000)
            
        except ccxt.NetworkError:
            attempts += 1
            print(f"    Network error (attempt {attempts}/{max_retries}), retrying...")
            time.sleep(30)
        except ccxt.ExchangeError as e:
            print(f"    Exchange error: {e}")
            break
    
    return all_candles


def fetch_2022_bitcoin_1min():
    """
    Fetch 2022 Bitcoin 1-minute data.
    
    Note: Most exchanges don't have 1-minute data that far back.
    We'll try Binance which has longer historical data.
    """
    print("\n" + "=" * 60)
    print("  FETCHING 2022 BITCOIN 1-MINUTE DATA")
    print("=" * 60)
    
    exchange = exchanges['binance']
    symbol = 'BTC/USDT'
    timeframe = '1m'
    
    start_date = "2022-01-01"
    end_date = "2022-12-31"
    
    start_ms = int(pd.Timestamp(start_date).timestamp() * 1000)
    end_ms = int(pd.Timestamp(end_date).timestamp() * 1000)
    
    print(f"\nTarget: {start_date} to {end_date}")
    print(f"Expected minutes: ~{int((end_ms - start_ms) / 60000):,}")
    
    # Binance has limits on historical data - try to get data in chunks
    # Binance 1m candles: ~500,000 per year, but API has limits
    
    print("\nNote: Binance API has limited historical 1m data.")
    print("Trying to fetch available data...")
    
    all_candles = []
    current_start = start_ms
    
    # Try to get data from a known working date
    # Binance typically has ~3-6 months of 1m data available
    
    print("\nFetching from 2022-07-01 to 2022-12-31 (second half of 2022)...")
    
    # Try to fetch from July 2022
    try:
        start_july = int(pd.Timestamp("2022-07-01").timestamp() * 1000)
        
        while start_july < end_ms:
            print(f"\n  Fetching from {pd.Timestamp(start_july, unit='ms')}...")
            
            candles = exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                since=start_july,
                limit=1000
            )
            
            if len(candles) == 0:
                break
            
            all_candles.extend(candles)
            last_ts = candles[-1][0]
            start_july = last_ts + 60000
            
            print(f"    Got {len(candles)} candles, total: {len(all_candles):,}")
            time.sleep(exchange.rateLimit / 1000)
            
    except Exception as e:
        print(f"  Error: {e}")
    
    if not all_candles:
        print("\n  No 2022 data available from Binance.")
        return None
    
    df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    print(f"\n  Fetched {len(df):,} candles from 2022")
    print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    return df


def fetch_2026_bitcoin_1min():
    """Fetch 2026 Bitcoin 1-minute data from Coinbase."""
    print("\n" + "=" * 60)
    print("  FETCHING 2026 BITCOIN 1-MINUTE DATA")
    print("=" * 60)
    
    exchange = exchanges['coinbase']
    symbol = 'BTC/USD'
    timeframe = '1m'
    
    # Fetch from Jan 1 to current date
    start_date = "2026-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    start_ms = int(pd.Timestamp(start_date).timestamp() * 1000)
    end_ms = int(pd.Timestamp(end_date).timestamp() * 1000)
    
    print(f"\nFetching from {start_date} to {end_date}...")
    
    all_candles = []
    current_start = start_ms
    
    while current_start < end_ms:
        print(f"\n  Fetching from {pd.Timestamp(current_start, unit='ms')}...")
        
        candles = exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            since=current_start,
            limit=1000
        )
        
        if len(candles) == 0:
            break
        
        all_candles.extend(candles)
        last_ts = candles[-1][0]
        current_start = last_ts + 60000
        
        print(f"    Got {len(candles)} candles, total: {len(all_candles):,}")
        time.sleep(exchange.rateLimit / 1000)
    
    if not all_candles:
        return None
    
    df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    print(f"\n  Fetched {len(df):,} candles from 2026")
    print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    return df


def main():
    print("=" * 70)
    print("  COMPREHENSIVE BITCOIN 1-MINUTE DATA FETCH")
    print("=" * 70)
    
    # Fetch 2026 data first (more likely to succeed)
    data_2026 = fetch_2026_bitcoin_1min()
    
    if data_2026 is not None:
        save_data(data_2026, "btc_1min_2026.csv")
    
    # Try to fetch 2022 data
    print("\n\n" + "=" * 60)
    print("  ATTEMPTING TO FETCH 2022 DATA")
    print("=" * 60)
    
    data_2022 = fetch_2022_bitcoin_1min()
    
    if data_2022 is not None:
        save_data(data_2022, "btc_1min_2022.csv")
    
    # Combine if both available
    if data_2026 is not None and data_2022 is not None:
        combined = pd.concat([data_2022, data_2026], ignore_index=True)
        combined = combined.sort_values('timestamp').reset_index(drop=True)
        save_data(combined, "btc_1min_2022_2026.csv")
        print(f"\nCombined: {len(combined):,} total candles")
    
    print("\n" + "=" * 70)
    print("  FETCH COMPLETE")
    print("=" * 70)
    print(f"\nData saved to: {DATA_DIR}")


def save_data(df: pd.DataFrame, filename: str):
    filepath = DATA_DIR / filename
    df.to_csv(filepath, index=False)
    print(f"  Saved: {filepath}")


if __name__ == "__main__":
    main()
