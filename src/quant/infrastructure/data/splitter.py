"""Data splitting utilities for rigorous backtesting.

This module provides chronological data splitting for time series backtesting:
- TRAIN: Used for hyperparameter optimization (grid search, etc.)
- VALIDATION: Single run only - no further tuning after this

No test set is used - the entire dataset is split into TRAIN and VALIDATION.
This ensures maximum data is used for training while still maintaining
proper temporal separation to prevent look-ahead bias.

Key Principles:
- Always use chronological splits for time series (older → newer)
- TRAIN must come before VALIDATION in time
- Never peek at VALIDATION during hyperparameter tuning
- If validation fails → discard strategy
"""

from typing import Tuple, Optional
import pandas as pd


def train_validation_split(
    data: pd.DataFrame,
    train_ratio: float = 0.8,
    timestamp_col: str = "timestamp",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split time series data into chronological train/validation sets.

    Args:
        data: DataFrame with time series data (must have timestamp column)
        train_ratio: Proportion of data to use for training (0-1)
        timestamp_col: Name of the timestamp column

    Returns:
        Tuple of (train_df, val_df) - chronologically ordered

    Example:
        >>> data = pd.read_csv("btc_1min.csv")
        >>> train, val = train_validation_split(data, train_ratio=0.8)
        >>> assert train["timestamp"].max() < val["timestamp"].min()
    """
    if not 0 < train_ratio < 1:
        raise ValueError(f"train_ratio must be between 0 and 1, got {train_ratio}")

    if timestamp_col not in data.columns:
        raise ValueError(f"Timestamp column '{timestamp_col}' not found in data")

    # Sort by timestamp to ensure chronological order
    data_sorted = data.sort_values(timestamp_col).reset_index(drop=True)

    # Calculate split point
    n = len(data_sorted)
    train_end = int(n * train_ratio)

    # Split chronologically
    train_df = data_sorted.iloc[:train_end].copy()
    val_df = data_sorted.iloc[train_end:].copy()

    # Verify chronological separation
    train_max = pd.to_datetime(train_df[timestamp_col]).max()
    val_min = pd.to_datetime(val_df[timestamp_col]).min()

    if train_max >= val_min:
        print(f"Warning: Train end ({train_max}) >= Val start ({val_min})")
        print("This may indicate duplicate timestamps or insufficient data")

    return train_df, val_df


def walk_forward_validation_split(
    data: pd.DataFrame,
    train_ratio: float = 0.7,
    window_size: Optional[int] = None,
    step_size: int = 1,
    timestamp_col: str = "timestamp",
) -> list:
    """
    Create walk-forward validation splits.

    For each window:
    - First `train_ratio` is used for training
    - Remaining is used for validation

    Args:
        data: DataFrame with time series data
        train_ratio: Proportion of window to use for training
        window_size: Size of each rolling window (default: full dataset)
        step_size: Step size between windows
        timestamp_col: Name of the timestamp column

    Returns:
        List of (train_df, val_df) tuples for each window
    """
    if window_size is None:
        window_size = len(data)

    data_sorted = data.sort_values(timestamp_col).reset_index(drop=True)
    n = len(data_sorted)

    if window_size > n:
        raise ValueError(f"window_size ({window_size}) > data length ({n})")

    splits = []
    start_idx = 0

    while start_idx + window_size <= n:
        window_data = data_sorted.iloc[start_idx : start_idx + window_size].copy()

        train_end = int(len(window_data) * train_ratio)
        train_df = window_data.iloc[:train_end].copy()
        val_df = window_data.iloc[train_end:].copy()

        splits.append((train_df, val_df))
        start_idx += step_size

    return splits


def create_train_validation_pipeline(
    data: pd.DataFrame,
    train_ratio: float = 0.8,
    timestamp_col: str = "timestamp",
    verbose: bool = True,
) -> dict:
    """
    Create a complete train/validation setup for backtesting.

    This is the main entry point for data splitting.

    Args:
        data: DataFrame with time series data
        train_ratio: Proportion for training (default: 0.8)
        timestamp_col: Name of timestamp column
        verbose: Print summary

    Returns:
        Dictionary with train/val dataframes and metadata
    """
    train_df, val_df = train_validation_split(
        data, train_ratio=train_ratio, timestamp_col=timestamp_col
    )

    result = {
        "train": train_df,
        "val": val_df,
        "train_ratio": train_ratio,
        "train_size": len(train_df),
        "val_size": len(val_df),
        "total_size": len(data),
        "train_start": train_df[timestamp_col].min(),
        "train_end": train_df[timestamp_col].max(),
        "val_start": val_df[timestamp_col].min(),
        "val_end": val_df[timestamp_col].max(),
    }

    if verbose:
        print("=" * 60)
        print("  DATA SPLIT SUMMARY")
        print("=" * 60)
        print(f"Train: {len(train_df):,} rows ({train_ratio*100:.1f}%)")
        print(f"  Period: {result['train_start']} to {result['train_end']}")
        print(f"Validation: {len(val_df):,} rows ({(1-train_ratio)*100:.1f}%)")
        print(f"  Period: {result['val_start']} to {result['val_end']}")

    return result


if __name__ == "__main__":
    # Quick test
    import numpy as np

    # Generate sample time series data
    dates = pd.date_range("2022-01-01", periods=1000, freq="1h")
    data = pd.DataFrame({
        "timestamp": dates,
        "close": np.random.randn(1000).cumsum() + 50000,
        "open": np.random.randn(1000).cumsum() + 50000,
        "high": np.random.randn(1000).cumsum() + 50100,
        "low": np.random.randn(1000).cumsum() + 49900,
        "volume": np.random.randint(100, 1000, 1000),
    })

    result = create_train_validation_pipeline(data, train_ratio=0.8)

    # Verify chronological split
    assert result["train_end"] < result["val_start"], "Chronological split failed!"
    print("\n✅ Chronological split verified!")
