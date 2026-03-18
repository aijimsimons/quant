"""Data generators for backtesting."""

import numpy as np
import pandas as pd


def generate_minute_bars(
    n_days: int = 30,
    start_price: float = 70000.0,
    volatility: float = 0.005,
    drift: float = 0.00005,
    minutes_per_day: int = 1440,
) -> pd.DataFrame:
    """Generate realistic minute-by-minute price data with volatility clustering."""
    np.random.seed(42)

    n_minutes = n_days * minutes_per_day

    prices = np.zeros(n_minutes)
    returns = np.zeros(n_minutes)
    volatility_process = np.zeros(n_minutes)

    prices[0] = start_price
    volatility_process[0] = volatility

    for t in range(1, n_minutes):
        volatility_process[t] = (
            0.1 * volatility + 0.85 * volatility_process[t - 1] + 0.05 * abs(returns[t - 1])
        )
        volatility_process[t] = max(volatility_process[t], volatility * 0.3)
        volatility_process[t] = min(volatility_process[t], volatility * 4)

        shock = np.random.normal(0, 1) * volatility_process[t]
        returns[t] = drift + shock
        prices[t] = prices[t - 1] * (1 + returns[t])
        prices[t] = max(prices[t], start_price * 0.3)
        prices[t] = min(prices[t], start_price * 3.0)

    # Create OHLC
    opens = np.zeros(n_minutes)
    highs = np.zeros(n_minutes)
    lows = np.zeros(n_minutes)
    closes = np.zeros(n_minutes)

    for t in range(n_minutes):
        if t == 0:
            opens[t] = start_price
            highs[t] = start_price * 1.001
            lows[t] = start_price * 0.999
            closes[t] = start_price * 1.0005
        else:
            close = prices[t]
            open_price = prices[t - 1]
            change = close - open_price

            if change >= 0:
                opens[t] = open_price
                closes[t] = close
                highs[t] = max(open_price, close) * (1 + np.random.uniform(0, 0.0005))
                lows[t] = min(open_price, close) * (1 - np.random.uniform(0, 0.0005))
            else:
                opens[t] = open_price
                closes[t] = close
                highs[t] = max(open_price, close) * (1 + np.random.uniform(0, 0.0005))
                lows[t] = min(open_price, close) * (1 - np.random.uniform(0, 0.0005))

    # Volume
    volumes = (1000 + 5000 * volatility_process).astype(int)

    timestamps = pd.date_range(start="2024-01-01 00:00:00", periods=n_minutes, freq="1min")

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
        }
    )


def generate_tick_data(
    n_days: int = 30,
    start_price: float = 70000.0,
    ticks_per_minute: int = 10,
) -> pd.DataFrame:
    """Generate tick-by-tick data."""
    np.random.seed(42)

    n_ticks = n_days * ticks_per_minute * 1440

    timestamps = []
    prices = []
    volumes = []

    current_price = start_price

    for _ in range(n_ticks):
        tick_time = pd.Timestamp("2024-01-01 00:00:00") + pd.Timedelta(
            microseconds=np.random.randint(0, n_ticks * 60_000_000)
        )
        timestamps.append(tick_time)

        price_move = np.random.normal(0, 5)
        current_price += price_move
        prices.append(max(current_price, 1000))
        volumes.append(np.random.randint(1, 10))

    df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "price": prices,
            "volume": volumes,
        }
    )

    return df.sort_values("timestamp").reset_index(drop=True)
