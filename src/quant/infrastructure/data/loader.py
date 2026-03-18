"""Data loading utilities."""

import pandas as pd
from typing import Optional


def load_from_csv(filepath: str) -> pd.DataFrame:
    """Load price data from CSV file."""
    df = pd.read_csv(filepath)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df.sort_values('timestamp').reset_index(drop=True)


def resample_to_bars(df: pd.DataFrame, freq: str = '5T') -> pd.DataFrame:
    """Resample tick data to OHLC bars."""
    df = df.set_index('timestamp')
    
    ohlc = df['price'].resample(freq).ohlc()
    volume = df['volume'].resample(freq).sum()
    
    result = pd.concat([ohlc, volume], axis=1)
    result.columns = ['open', 'high', 'low', 'close', 'volume']
    result = result.reset_index()
    
    return result.dropna()
