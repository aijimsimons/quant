"""Mean reversion strategy optimized for Polymarket 5-minute binary markets.

Polymarket-specific adaptations:
- Binary outcomes (0-100 range) - prices revert toward 50 (50/50 probability)
- Higher volatility than traditional assets
- Shorter holding periods needed (markets resolve quickly)
- Transaction costs eat into small price movements

Optimal parameters (from grid search):
- window: 30 periods
- std_multiplier: 1.0-2.0 (no significant difference)
- min_zscore: -1.2
- max_zscore: 1.1
"""

from typing import Union

import numpy as np
import pandas as pd
import polars as pl


def mean_reversion_polymarket(
    data: Union[pl.LazyFrame, pl.DataFrame, pd.DataFrame],
    capital: float = 10000.0,
    window: int = 30,
    std_multiplier: float = 1.5,
    position_size_pct: float = 0.05,
    stop_loss_pct: float = 0.02,
    take_profit_pct: float = 0.03,
    max_holding_period: int = 20,
    min_zscore: float = -1.2,
    max_zscore: float = 1.1,
    slippage_pct: float = 0.001,
    commission: float = 0.0,
    verbose: bool = False,
) -> Union[pl.LazyFrame, pl.DataFrame]:
    """
    Mean reversion strategy for Polymarket binary options.

    Key differences from regular crypto mean reversion:
    - Z-score thresholds are tighter (±0.8 vs ±1.0) because binary markets move faster
    - Shorter holding period (100 min vs 60 min) because markets resolve quickly
    - Price target is 50 (neutral probability) not SMA
    - Higher volatility means wider bands needed

    Entries:
    - Long when zscore < -0.8 (price << 50, probability underestimated)
    - Short when zscore > 0.8 (price >> 50, probability overestimated)

    Exits:
    - Stop loss or take profit
    - Maximum holding period
    - Price returns to neutral (50) before holding period ends
    """
    # Convert to polars if needed
    if isinstance(data, pd.DataFrame):
        df = pl.from_pandas(data).lazy()
    elif isinstance(data, pl.DataFrame):
        df = data.lazy()
    else:
        df = data

    # Calculate Bollinger Bands around 50 (neutral probability for binary markets)
    df = df.with_columns(
        [
            (pl.col("close") - pl.lit(50)).rolling_mean(window).alias("deviation_sma"),
        ]
    )

    # Calculate std of deviation from 50
    df = df.with_columns(
        [
            (pl.col("close") - pl.lit(50)).rolling_std(window).alias("deviation_std"),
        ]
    )

    # Calculate Z-score of deviation from 50
    df = df.with_columns(
        [
            ((pl.col("close") - pl.lit(50)) / pl.col("deviation_std")).alias("zscore"),
        ]
    )

    # Generate signals - use shift(1) to avoid look-ahead bias
    df = df.with_columns(
        [
            pl.when(pl.col("zscore").shift(1) < min_zscore)
            .then(pl.lit(1))
            .when(pl.col("zscore").shift(1) > max_zscore)
            .then(pl.lit(-1))
            .otherwise(pl.lit(0))
            .alias("signal")
        ]
    )

    # For backtesting with position tracking, we need to collect to DataFrame
    df_eager = df.collect()

    # Convert to numpy for efficient position tracking
    n = len(df_eager)
    positions = np.zeros(n, dtype=np.float64)
    entry_prices = np.zeros(n, dtype=np.float64)
    entry_times = np.zeros(n, dtype=np.float64)
    pnl = np.zeros(n, dtype=np.float64)

    position = 0
    entry_price = 0.0
    entry_time = 0

    for i in range(window + 1, n):  # +1 because of shift(1)
        current_price = df_eager["close"][i]
        current_signal = df_eager["signal"][i]

        if position == 0:
            # Entry logic - trade on NEXT bar after signal
            if current_signal == 1:
                # Long: price far below 50 (probability underestimated)
                position_value = capital * position_size_pct
                # Apply slippage to entry price
                entry_price = current_price * (1 - slippage_pct)
                position = int(position_value / entry_price)
                # Ensure we don't exceed capital
                if position * entry_price > capital:
                    position = int(capital / entry_price)
                entry_time = i
                if verbose:
                    print(
                        f"   Entry LONG at i={i}, price={current_price:.2f}, "
                        f"entry_price={entry_price:.2f}, position={position}"
                    )

            elif current_signal == -1:
                # Short: price far above 50 (probability overestimated)
                position_value = capital * position_size_pct
                # Apply slippage to entry price
                entry_price = current_price * (1 + slippage_pct)
                position = -int(position_value / abs(entry_price))
                # Ensure we don't exceed capital
                if abs(position) * entry_price > capital:
                    position = -int(capital / entry_price)
                entry_time = i
                if verbose:
                    print(
                        f"   Entry SHORT at i={i}, price={current_price:.2f}, "
                        f"entry_price={entry_price:.2f}, position={position}"
                    )

        else:
            # Calculate P&L based on position direction
            if position > 0:  # Long position
                pnl_per_unit = current_price - entry_price
            else:  # Short position
                pnl_per_unit = entry_price - current_price

            current_pnl = pnl_per_unit * abs(position)

            # Check exit conditions
            if current_pnl <= -capital * stop_loss_pct:
                positions[i] = 0
                pnl[i] = current_pnl
                position = 0
                entry_price = 0.0
                if verbose:
                    print(f"   STOP LOSS at i={i}, P&L=${current_pnl:.2f}")

            elif current_pnl >= capital * take_profit_pct:
                positions[i] = 0
                pnl[i] = current_pnl
                position = 0
                entry_price = 0.0
                if verbose:
                    print(f"   TAKE PROFIT at i={i}, P&L=${current_pnl:.2f}")

            elif i - entry_time >= max_holding_period:
                positions[i] = 0
                pnl[i] = current_pnl
                position = 0
                entry_price = 0.0
                if verbose:
                    print(f"   TIME EXIT at i={i}, P&L=${current_pnl:.2f}")

            elif abs(current_price - 50) < 1.0 and abs(current_price - entry_price) > 0.5:
                # Price returned to neutral (50) - take profit
                positions[i] = 0
                pnl[i] = current_pnl
                position = 0
                entry_price = 0.0
                if verbose:
                    print(f"   NEUTRAL EXIT at i={i}, P&L=${current_pnl:.2f}")

            else:
                positions[i] = float(position)
                entry_prices[i] = entry_price
                entry_times[i] = float(entry_time)

    # Add results to DataFrame
    df_eager = df_eager.with_columns(
        [
            pl.Series("position", positions),
            pl.Series("entry_price", entry_prices),
            pl.Series("entry_time", entry_times),
            pl.Series("pnl", pnl),
        ]
    )

    # Calculate metrics using polars
    df_eager = df_eager.with_columns(
        [
            pl.col("pnl").cum_sum().alias("cumulative_pnl"),
        ]
    )

    df_eager = df_eager.with_columns(
        [
            (pl.lit(capital) + pl.col("cumulative_pnl")).alias("equity"),
        ]
    )

    df_eager = df_eager.with_columns(
        [
            pl.col("equity").pct_change().alias("returns"),
        ]
    )

    df_eager = df_eager.with_columns(
        [
            (pl.lit(1) + pl.col("returns")).cum_prod().alias("cumulative_returns"),
        ]
    )

    return df_eager


def calculate_metrics(df: Union[pl.DataFrame, pd.DataFrame], capital: float = 10000.0) -> dict:
    """Calculate strategy performance metrics."""
    # Convert to polars if needed
    if isinstance(df, pd.DataFrame):
        df = pl.from_pandas(df)

    returns = df["returns"].drop_nulls()

    if len(returns) == 0 or returns.std() == 0:
        sharpe = 0.0
    else:
        # Annualize for 5-minute data: 252 days * 24 hours * 12 five-min periods
        annualization_factor = (252 * 24 * 12) ** 0.5
        sharpe = (returns.mean() / returns.std()) * annualization_factor

    equity = df["equity"]
    rolling_max = equity.cum_max()
    drawdown = (rolling_max - equity) / rolling_max
    max_dd = drawdown.max() if len(drawdown) > 1 else 0

    wins = df.filter(pl.col("pnl") > 0)["pnl"]
    losses = df.filter(pl.col("pnl") < 0)["pnl"]
    win_rate = (
        len(wins) / len(df.filter(pl.col("pnl") != 0))
        if len(df.filter(pl.col("pnl") != 0)) > 0
        else 0
    )
    profit_factor = (
        abs(wins.sum() / losses.sum()) if len(losses) > 0 and losses.sum() != 0 else float("inf")
    )

    position_changes = df["position"].diff().abs().sum()
    total_trades = int(position_changes // 2) if position_changes > 0 else 0

    avg_win = wins.mean() if len(wins) > 0 else 0.0
    avg_loss = losses.mean() if len(losses) > 0 else 0.0

    return {
        "total_return": (equity[-1] - capital) / capital if len(equity) > 1 else 0,
        "sharpe_ratio": sharpe,
        "max_drawdown": max_dd,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "total_trades": total_trades,
        "avg_win": float(avg_win),
        "avg_loss": float(avg_loss),
    }
