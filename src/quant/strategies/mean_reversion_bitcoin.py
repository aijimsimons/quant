"""Mean reversion strategy for Bitcoin (actual price data, not binary markets).

This strategy uses actual Bitcoin OHLCV data and applies mean reversion
around a moving average, which is more appropriate for crypto than
the Polymarket-specific strategy that targets 50.
"""

from typing import Union

import numpy as np
import pandas as pd
import polars as pl


def mean_reversion_bitcoin(
    data: Union[pl.LazyFrame, pl.DataFrame, pd.DataFrame],
    capital: float = 10000.0,
    window: int = 20,
    std_multiplier: float = 2.0,
    position_size_pct: float = 0.05,
    stop_loss_pct: float = 0.02,
    take_profit_pct: float = 0.03,
    max_holding_period: int = 20,
    min_zscore: float = -2.0,
    max_zscore: float = 2.0,
    slippage_pct: float = 0.001,
    commission: float = 0.0,
    verbose: bool = False,
) -> Union[pl.LazyFrame, pl.DataFrame]:
    """
    Mean reversion strategy for Bitcoin price data.
    
    This strategy uses Bollinger Bands around the SMA to identify
    oversold/overbought conditions in actual Bitcoin price data.
    
    Entries:
    - Long when zscore < -2.0 (price far below SMA)
    - Short when zscore > 2.0 (price far above SMA)
    
    Exits:
    - Stop loss or take profit
    - Maximum holding period
    
    Args:
        data: DataFrame with OHLCV data
        capital: Initial capital
        window: Lookback window for SMA/std
        std_multiplier: Std deviation multiplier for bands
        position_size_pct: Position size as % of capital
        stop_loss_pct: Stop loss as % of position
        take_profit_pct: Take profit as % of position
        max_holding_period: Max bars to hold
        min_zscore: Lower zscore threshold
        max_zscore: Upper zscore threshold
        slippage_pct: Slippage on entry
        commission: Commission per trade
        verbose: Print debug info
        
    Returns:
        DataFrame with strategy results
    """
    # Convert to polars if needed
    if isinstance(data, pd.DataFrame):
        df = pl.from_pandas(data).lazy()
    elif isinstance(data, pl.DataFrame):
        df = data.lazy()
    else:
        df = data

    # Calculate Bollinger Bands around SMA
    df = df.with_columns([
        pl.col('close').rolling_mean(window).alias('sma'),
        pl.col('close').rolling_std(window).alias('std'),
    ])

    # Calculate Z-score
    df = df.with_columns([
        ((pl.col('close') - pl.col('sma')) / pl.col('std')).alias('zscore'),
    ])

    # Generate signals - use shift(1) to avoid look-ahead bias
    df = df.with_columns([
        pl.when(pl.col('zscore').shift(1) < min_zscore).then(pl.lit(1))
        .when(pl.col('zscore').shift(1) > max_zscore).then(pl.lit(-1))
        .otherwise(pl.lit(0)).alias('signal')
    ])

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

    for i in range(window + 1, n):
        current_price = df_eager['close'][i]
        current_signal = df_eager['signal'][i]

        if position == 0:
            # Entry logic - trade on NEXT bar after signal
            if current_signal == 1:
                # Long: price far below SMA
                position_value = capital * position_size_pct
                entry_price = current_price * (1 + slippage_pct)  # Buy at higher price
                # Use float positions for crypto to handle fractional units
                position = position_value / entry_price
                if position * entry_price > capital:
                    position = capital / entry_price
                entry_time = i
                if verbose:
                    print(
                        f"   Entry LONG at i={i}, price={current_price:.2f}, "
                        f"entry_price={entry_price:.2f}, position={position:.4f} units"
                    )

            elif current_signal == -1:
                # Short: price far above SMA
                position_value = capital * position_size_pct
                entry_price = current_price * (1 - slippage_pct)  # Sell at lower price
                # Use float positions for crypto to handle fractional units
                position = -(position_value / entry_price)
                if abs(position) * entry_price > capital:
                    position = -(capital / entry_price)
                entry_time = i
                if verbose:
                    print(
                        f"   Entry SHORT at i={i}, price={current_price:.2f}, "
                        f"entry_price={entry_price:.2f}, position={position:.4f} units"
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

            else:
                positions[i] = float(position)
                entry_prices[i] = entry_price
                entry_times[i] = float(entry_time)

    # Add results to DataFrame
    df_eager = df_eager.with_columns([
        pl.Series('position', positions),
        pl.Series('entry_price', entry_prices),
        pl.Series('entry_time', entry_times),
        pl.Series('pnl', pnl),
    ])

    # Calculate metrics
    df_eager = df_eager.with_columns([
        pl.col('pnl').cum_sum().alias('cumulative_pnl'),
    ])

    df_eager = df_eager.with_columns([
        (pl.lit(capital) + pl.col('cumulative_pnl')).alias('equity'),
    ])

    df_eager = df_eager.with_columns([
        pl.col('equity').pct_change().alias('returns'),
    ])

    df_eager = df_eager.with_columns([
        (pl.lit(1) + pl.col('returns')).cum_prod().alias('cumulative_returns'),
    ])

    return df_eager


def calculate_metrics(df: Union[pl.DataFrame, pd.DataFrame], capital: float = 10000.0) -> dict:
    """Calculate strategy performance metrics."""
    if isinstance(df, pd.DataFrame):
        df = pl.from_pandas(df)

    returns = df['returns'].drop_nulls()

    if len(returns) == 0 or returns.std() == 0:
        sharpe = 0.0
    else:
        # Annualize for 5-minute data
        annualization_factor = (252 * 24 * 12) ** 0.5
        sharpe = (returns.mean() / returns.std()) * annualization_factor

    equity = df['equity']
    rolling_max = equity.cum_max()
    drawdown = (rolling_max - equity) / rolling_max
    max_dd = drawdown.max() if len(drawdown) > 1 else 0

    wins = df.filter(pl.col('pnl') > 0)['pnl']
    losses = df.filter(pl.col('pnl') < 0)['pnl']
    win_rate = len(wins) / len(df.filter(pl.col('pnl') != 0)) if len(df.filter(pl.col('pnl') != 0)) > 0 else 0
    profit_factor = abs(wins.sum() / losses.sum()) if len(losses) > 0 and losses.sum() != 0 else float('inf')

    position_changes = df['position'].diff().abs().sum()
    total_trades = int(position_changes // 2) if position_changes > 0 else 0

    avg_win = wins.mean() if len(wins) > 0 else 0.0
    avg_loss = losses.mean() if len(losses) > 0 else 0.0

    return {
        'total_return': (equity[-1] - capital) / capital if len(equity) > 1 else 0,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_dd,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'total_trades': total_trades,
        'avg_win': float(avg_win),
        'avg_loss': float(avg_loss),
    }
