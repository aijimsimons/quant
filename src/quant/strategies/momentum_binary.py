"""Momentum strategy optimized for 5-minute binary markets.

Binary market specific adaptations:
- Price range 0-100 (probability-like)
- Mean-reverting tendency but with trend phases
- Shorter holding periods (5-15 bars = 25-75 minutes)
- Tighter stops and takes due to high volatility
- Volume proxy: open interest or transaction count
"""

import numpy as np
import pandas as pd
from typing import Union


def momentum_binary(
    data: Union[pd.DataFrame, np.ndarray],
    capital: float = 10000.0,
    fast_window: int = 3,
    slow_window: int = 10,
    momentum_threshold: float = 0.002,  # 0.2% price movement
    volume_threshold: float = 1.3,      # 30% above average volume
    position_size_pct: float = 0.05,    # 5% of capital per trade
    stop_loss_pct: float = 0.015,       # 1.5% stop loss
    take_profit_pct: float = 0.025,     # 2.5% take profit
    max_holding_period: int = 15,       # 15 five-minute bars = 75 minutes
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Momentum strategy for 5-minute binary markets.

    Entry Logic:
    - LONG: Price > MA, momentum positive and strong, volume elevated
    - SHORT: Price < MA, momentum negative and strong, volume elevated

    Binary Market Specifics:
    - Target price range: 0-100
    - Neutral zone: 45-55 (avoid trading near center)
    - Extreme zones: <40 or >60 (strong momentum zones)

    Args:
        data: DataFrame with OHLCV or numpy array
        capital: Initial capital
        fast_window: Fast MA window (3-10 for 5-min)
        slow_window: Slow MA window (10-30 for 5-min)
        momentum_threshold: Minimum momentum for entry
        volume_threshold: Volume multiplier for confirmation
        position_size_pct: Capital per trade
        stop_loss_pct: Stop loss percentage
        take_profit_pct: Take profit percentage
        max_holding_period: Max bars to hold
        verbose: Print details

    Returns:
        DataFrame with positions, P&L, and metrics
    """
    # Convert to DataFrame if needed
    if isinstance(data, np.ndarray):
        data = pd.DataFrame(
            data,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )

    df = data.copy()

    # Calculate MAs
    df['fast_ma'] = df['close'].rolling(window=fast_window).mean()
    df['slow_ma'] = df['close'].rolling(window=slow_window).mean()

    # Calculate momentum (rate of change)
    df['momentum'] = df['close'].pct_change(periods=fast_window)

    # Volume average
    df['volume_ma'] = df['volume'].rolling(window=slow_window).mean()

    # Binary market specific: distance from neutral (50)
    df['distance_from_50'] = np.abs(df['close'] - 50.0)

    # Generate signals
    df['signal'] = 0

    # LONG: Price above slow MA, positive momentum, elevated volume
    # AND price in extreme zone (>55) for stronger momentum
    df.loc[
        (df['close'] > df['slow_ma'])
        & (df['momentum'] > momentum_threshold)
        & (df['volume'] > volume_threshold * df['volume_ma'])
        & (df['close'] > 55),  # Binary market: trade on extremes
        'signal'
    ] = 1

    # SHORT: Price below slow MA, negative momentum, elevated volume
    # AND price in extreme zone (<45)
    df.loc[
        (df['close'] < df['slow_ma'])
        & (df['momentum'] < -momentum_threshold)
        & (df['volume'] > volume_threshold * df['volume_ma'])
        & (df['close'] < 45),  # Binary market: trade on extremes
        'signal'
    ] = -1

    # Pre-allocate arrays for position tracking
    n = len(df)
    positions = np.zeros(n, dtype=np.float64)
    entry_prices = np.zeros(n, dtype=np.float64)
    entry_times = np.zeros(n, dtype=np.float64)
    pnl = np.zeros(n, dtype=np.float64)

    position = 0
    entry_price = 0.0
    entry_time = 0

    for i in range(slow_window, n):
        if position == 0:
            # Entry logic
            if df.loc[i, 'signal'] == 1:
                # LONG entry
                position_value = capital * position_size_pct
                price = df.loc[i, 'close']
                position = max(1, int(position_value / price))
                entry_price = price
                entry_time = i
                if verbose:
                    print(f"   Entry LONG at i={i}, price={price:.2f}, position={position}")

            elif df.loc[i, 'signal'] == -1:
                # SHORT entry
                position_value = capital * position_size_pct
                price = df.loc[i, 'close']
                position = -max(1, int(position_value / abs(price)))
                entry_price = price
                entry_time = i
                if verbose:
                    print(f"   Entry SHORT at i={i}, price={price:.2f}, position={position}")

        else:
            # Position active - calculate P&L
            current_price = df.loc[i, 'close']
            if position > 0:  # Long position
                pnl_per_unit = current_price - entry_price
            else:  # Short position
                pnl_per_unit = entry_price - current_price

            current_pnl = pnl_per_unit * abs(position)

            # Check exit conditions
            if current_pnl <= -capital * stop_loss_pct:
                # Stop loss hit
                positions[i] = 0
                pnl[i] = current_pnl
                position = 0
                entry_price = 0.0
                if verbose:
                    print(f"   STOP LOSS at i={i}, P&L=${current_pnl:.2f}")

            elif current_pnl >= capital * take_profit_pct:
                # Take profit hit
                positions[i] = 0
                pnl[i] = current_pnl
                position = 0
                entry_price = 0.0
                if verbose:
                    print(f"   TAKE PROFIT at i={i}, P&L=${current_pnl:.2f}")

            elif i - entry_time >= max_holding_period:
                # Max holding period reached
                positions[i] = 0
                pnl[i] = current_pnl
                position = 0
                entry_price = 0.0
                if verbose:
                    print(f"   TIME EXIT at i={i}, P&L=${current_pnl:.2f}")

            else:
                # Continue holding
                positions[i] = float(position)
                entry_prices[i] = entry_price
                entry_times[i] = float(entry_time)

    # Add results to DataFrame
    df['position'] = positions
    df['entry_price'] = entry_prices
    df['entry_time'] = entry_times
    df['pnl'] = pnl

    # Calculate equity and returns
    df['cumulative_pnl'] = df['pnl'].cumsum()
    df['equity'] = capital + df['cumulative_pnl']
    df['returns'] = df['equity'].pct_change()
    df['cumulative_returns'] = (1 + df['returns']).cumprod()

    return df


def calculate_binary_metrics(df: pd.DataFrame, capital: float = 10000.0) -> dict:
    """
    Calculate performance metrics for binary market momentum strategy.

    Args:
        df: DataFrame with strategy results
        capital: Initial capital

    Returns:
        Dictionary with performance metrics
    """
    returns = df['returns'].dropna()

    if len(returns) == 0 or returns.std() == 0:
        sharpe = 0.0
    else:
        # Annualize: 252 days * 24 hours * 12 five-min periods = 72576 periods
        annualization_factor = (252 * 24 * 12) ** 0.5
        sharpe = (returns.mean() / returns.std()) * annualization_factor

    equity = df['equity']
    rolling_max = equity.cummax()
    drawdown = (rolling_max - equity) / rolling_max
    max_dd = drawdown.max() if len(drawdown) > 1 else 0

    wins = df[df['pnl'] > 0]['pnl']
    losses = df[df['pnl'] < 0]['pnl']
    win_rate = len(wins) / len(df[df['pnl'] != 0]) if len(df[df['pnl'] != 0]) > 0 else 0
    profit_factor = abs(wins.sum() / losses.sum()) if len(losses) > 0 and losses.sum() != 0 else float('inf')

    position_changes = df['position'].diff().abs().sum()
    total_trades = int(position_changes // 2) if position_changes > 0 else 0

    avg_win = wins.mean() if len(wins) > 0 else 0.0
    avg_loss = losses.mean() if len(losses) > 0 else 0.0

    return {
        'total_return': (equity.iloc[-1] - capital) / capital if len(equity) > 1 else 0,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_dd,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'total_trades': total_trades,
        'avg_win': float(avg_win),
        'avg_loss': float(avg_loss),
    }


if __name__ == "__main__":
    # Quick test with synthetic binary data
    import random

    # Generate 5-minute binary market data (0-100 range)
    np.random.seed(42)
    n_periods = 1000

    prices = [50.0]
    for _ in range(1, n_periods):
        change = random.uniform(-2, 2)  # 5-min volatility
        prices.append(max(0, min(100, prices[-1] + change)))

    data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=n_periods, freq='5min'),
        'open': prices[:-1],
        'high': [max(o, c) + random.uniform(0, 1) for o, c in zip(prices[:-1], prices[1:])],
        'low': [min(o, c) - random.uniform(0, 1) for o, c in zip(prices[:-1], prices[1:])],
        'close': prices[1:],
        'volume': [random.randint(100, 1000) for _ in range(n_periods)],
    })

    print("Testing momentum binary strategy...")
    result = momentum_binary(data, capital=10000.0, verbose=True)
    metrics = calculate_binary_metrics(result, capital=10000.0)

    print("\n" + "=" * 50)
    print("PERFORMANCE METRICS")
    print("=" * 50)
    print(f"Total Return: {metrics['total_return']*100:+.2f}%")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {metrics['max_drawdown']*100:+.2f}%")
    print(f"Win Rate: {metrics['win_rate']*100:.2f}%")
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
