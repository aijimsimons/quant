"""Data module."""

from quant.infrastructure.data.generator import generate_minute_bars, generate_tick_data
from quant.infrastructure.data.loader import load_from_csv, resample_to_bars
from quant.infrastructure.data.real_data import (
    generate_historical_polymarket_data,
    generate_polymarket_with_2024_events,
    generate_multiple_market_scenarios,
    load_bitcoin_ohlcv_csv,
    fetch_bitcoin_ohlcv,
    load_bitcoin_1min_csv,
    get_bitcoin_1min_data,
)
from quant.infrastructure.data.splitter import (
    train_validation_split,
    walk_forward_validation_split,
    create_train_validation_pipeline,
)

__all__ = [
    "generate_minute_bars",
    "generate_tick_data",
    "load_from_csv",
    "resample_to_bars",
    "generate_historical_polymarket_data",
    "generate_polymarket_with_2024_events",
    "generate_multiple_market_scenarios",
    "load_bitcoin_ohlcv_csv",
    "fetch_bitcoin_ohlcv",
    "load_bitcoin_1min_csv",
    "get_bitcoin_1min_data",
    "train_validation_split",
    "walk_forward_validation_split",
    "create_train_validation_pipeline",
]
