"""Mean reversion strategy using Bollinger Bands."""

import pandas as pd
import numpy as np
from typing import Optional


def mean_reversion_strategy(
    data: pd.DataFrame,
    capital: float = 10000.0,
    window: int = 20,
    std_multiplier: float = 2.0,
    position_size_pct: float = 0.05,
    stop_loss_pct: float = 0.015,
    take_profit_pct: float = 0.025,
    max_holding_period: int = 60,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Mean reversion strategy using Bollinger Bands.
    
    Entries:
    - Long when zscore < -1.0 (oversold)
    - Short when zscore > 1.0 (overbought)
    
    Exits:
    - Stop loss or take profit
    - Maximum holding period
    """
    df = data.copy()
    
    # Calculate Bollinger Bands
    df['sma'] = df['close'].rolling(window=window).mean()
    df['std'] = df['close'].rolling(window=window).std()
    df['upper_band'] = df['sma'] + std_multiplier * df['std']
    df['lower_band'] = df['sma'] - std_multiplier * df['std']
    
    # Calculate Z-score
    df['zscore'] = (df['close'] - df['sma']) / df['std']
    
    # Generate signals
    df['signal'] = 0
    df.loc[df['zscore'] < -1.0, 'signal'] = 1  # Long
    df.loc[df['zscore'] > 1.0, 'signal'] = -1  # Short
    
    # Pre-allocate arrays
    n = len(df)
    positions = np.zeros(n, dtype=np.float64)
    entry_prices = np.zeros(n, dtype=np.float64)
    entry_times = np.zeros(n, dtype=np.float64)
    pnl = np.zeros(n, dtype=np.float64)
    
    # Strategy state
    position = 0
    entry_price = 0.0
    entry_time = 0
    
    for i in range(window, n):
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
            
            # Stop loss
            if current_pnl <= -capital * stop_loss_pct:
                positions[i] = 0
                pnl[i] = current_pnl
                position = 0
                entry_price = 0.0
                
            # Take profit
            elif current_pnl >= capital * take_profit_pct:
                positions[i] = 0
                pnl[i] = current_pnl
                position = 0
                entry_price = 0.0
                
            # Max holding period
            elif i - entry_time >= max_holding_period:
                positions[i] = 0
                pnl[i] = current_pnl
                position = 0
                entry_price = 0.0
                
            else:
                positions[i] = float(position)
                entry_prices[i] = entry_price
                entry_times[i] = float(entry_time)
    
    # Assign to DataFrame
    df['position'] = positions
    df['entry_price'] = entry_prices
    df['entry_time'] = entry_times
    df['pnl'] = pnl
    
    # Calculate metrics
    df['cumulative_pnl'] = df['pnl'].cumsum()
    df['equity'] = capital + df['cumulative_pnl']
    df['returns'] = df['equity'].pct_change()
    df['cumulative_returns'] = (1 + df['returns']).cumprod()
    
    return df


def calculate_metrics(df: pd.DataFrame, capital: float = 10000.0) -> dict:
    """Calculate strategy performance metrics."""
    returns = df['returns'].dropna()
    
    if len(returns) == 0 or returns.std() == 0:
        sharpe = 0.0
    else:
        sharpe = (returns.mean() / returns.std()) * (252 * 24) ** 0.5
    
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
