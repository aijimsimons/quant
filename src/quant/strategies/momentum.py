"""Momentum breakout strategy."""

import pandas as pd
import numpy as np
from typing import Optional


def momentum_strategy(
    data: pd.DataFrame,
    capital: float = 10000.0,
    fast_window: int = 5,
    slow_window: int = 20,
    volume_threshold: float = 1.5,
    position_size_pct: float = 0.05,
    stop_loss_pct: float = 0.015,
    take_profit_pct: float = 0.03,
    max_holding_period: int = 60,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Momentum breakout strategy using MA crossover and volume confirmation.
    """
    df = data.copy()
    
    # Calculate MAs
    df['fast_ma'] = df['close'].rolling(window=fast_window).mean()
    df['slow_ma'] = df['close'].rolling(window=slow_window).mean()
    df['volume_ma'] = df['volume'].rolling(window=slow_window).mean()
    
    # Momentum
    df['momentum'] = df['close'].pct_change(periods=fast_window)
    
    # Generate signals
    df['signal'] = 0
    
    # Long: above slow MA, fast above slow, high volume, positive momentum
    df.loc[
        (df['close'] > df['slow_ma']) &
        (df['fast_ma'] > df['slow_ma']) &
        (df['volume'] > volume_threshold * df['volume_ma']) &
        (df['momentum'] > 0),
        'signal'
    ] = 1
    
    # Short: below slow MA, fast below slow, high volume, negative momentum
    df.loc[
        (df['close'] < df['slow_ma']) &
        (df['fast_ma'] < df['slow_ma']) &
        (df['volume'] > volume_threshold * df['volume_ma']) &
        (df['momentum'] < 0),
        'signal'
    ] = -1
    
    # Pre-allocate
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
            if df.loc[i, 'signal'] == 1:
                position_value = capital * position_size_pct
                price = df.loc[i, 'close']
                position = max(1, int(position_value / price))
                entry_price = price
                entry_time = i
                if verbose:
                    print(f"   Entry LONG at i={i}, price={entry_price:.2f}, position={position}")
                
            elif df.loc[i, 'signal'] == -1:
                position_value = capital * position_size_pct
                price = df.loc[i, 'close']
                position = -max(1, int(position_value / price))
                entry_price = price
                entry_time = i
                if verbose:
                    print(f"   Entry SHORT at i={i}, price={entry_price:.2f}, position={position}")
                
        else:
            current_price = df.loc[i, 'close']
            pnl_per_unit = current_price - entry_price if position > 0 else entry_price - current_price
            current_pnl = pnl_per_unit * abs(position)
            
            if current_pnl <= -capital * stop_loss_pct:
                positions[i] = 0
                pnl[i] = current_pnl
                position = 0
                entry_price = 0.0
                
            elif current_pnl >= capital * take_profit_pct:
                positions[i] = 0
                pnl[i] = current_pnl
                position = 0
                entry_price = 0.0
                
            elif i - entry_time >= max_holding_period:
                positions[i] = 0
                pnl[i] = current_pnl
                position = 0
                entry_price = 0.0
                
            else:
                positions[i] = float(position)
                entry_prices[i] = entry_price
                entry_times[i] = float(entry_time)
    
    df['position'] = positions
    df['entry_price'] = entry_prices
    df['entry_time'] = entry_times
    df['pnl'] = pnl
    
    df['cumulative_pnl'] = df['pnl'].cumsum()
    df['equity'] = capital + df['cumulative_pnl']
    df['returns'] = df['equity'].pct_change()
    df['cumulative_returns'] = (1 + df['returns']).cumprod()
    
    return df
