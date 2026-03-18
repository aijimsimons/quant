"""Mean reversion strategy optimized for Bitcoin.

Key assumption: Bitcoin exhibits mean reversion over shorter timeframes (5-15 days)
despite its long-term trending behavior.

Strategy:
1. Calculate Bollinger Bands on 5-15 day window
2. Enter long when price is 1.0-1.5 std below SMA (oversold)
3. Enter short when price is 1.0-1.5 std above SMA (overbought)
4. Exit on stop loss (1-2%), take profit (2-3%), or max holding (30 days)
5. Position sizing: 2-5% of capital per trade

Parameters optimized for Bitcoin's volatility:
- Shorter window (10-20 days) captures intramonth mean reversion
- Tighter z-scores (±1.0 to ±1.5) generate more signals
- Moderate stop loss (1-2%) prevents large drawdowns
- Reasonable take profit (2-3%) captures mean reversion moves
"""

from typing import Tuple
import numpy as np
import pandas as pd
import polars as pl


def calculate_bollinger_bands(
    prices: np.ndarray,
    window: int = 20,
    num_std: float = 2.0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate Bollinger Bands for price series.
    
    Args:
        prices: Price series
        window: Rolling window size
        num_std: Number of standard deviations for bands
        
    Returns:
        Tuple of (sma, upper_band, lower_band)
    """
    sma = pd.Series(prices).rolling(window=window).mean().values
    std = pd.Series(prices).rolling(window=window).std().values
    
    # Handle NaN values
    sma = np.where(np.isnan(sma), prices, sma)
    std = np.where(np.isnan(std), 0, std)
    
    upper_band = sma + num_std * std
    lower_band = sma - num_std * std
    
    return sma, upper_band, lower_band


def calculate_zscore(
    price: float,
    sma: float,
    std: float,
) -> float:
    """Calculate z-score for price relative to SMA.
    
    Args:
        price: Current price
        sma: Simple moving average
        std: Standard deviation
        
    Returns:
        Z-score (positive = above SMA, negative = below SMA)
    """
    if std == 0:
        return 0.0
    return (price - sma) / std


def mean_reversion_bitcoin(
    data: pl.DataFrame,
    capital: float = 10000.0,
    window: int = 15,  # Shorter window for Bitcoin
    std_multiplier: float = 1.5,  # Tighter bands
    min_zscore: float = -1.0,  # Enter long when z < -1.0
    max_zscore: float = 1.0,   # Enter short when z > 1.0
    stop_loss_pct: float = 0.02,  # 2% stop loss
    take_profit_pct: float = 0.03,  # 3% take profit
    max_holding_period: int = 30,  # Max 30 days per trade
    position_size_pct: float = 0.05,  # 5% of capital per trade
    slippage_pct: float = 0.001,  # 0.1% slippage
    verbose: bool = False,
) -> pl.DataFrame:
    """Run mean reversion strategy on Bitcoin OHLCV data.
    
    Args:
        data: Polars DataFrame with columns: timestamp, open, high, low, close, volume
        capital: Initial capital in USD
        window: Rolling window for Bollinger Bands
        std_multiplier: Number of std deviations for bands
        min_zscore: Z-score threshold for long entry (negative)
        max_zscore: Z-score threshold for short entry (positive)
        stop_loss_pct: Stop loss as fraction of capital
        take_profit_pct: Take profit as fraction of capital
        max_holding_period: Max days to hold position
        position_size_pct: Fraction of capital to use per trade
        slippage_pct: Slippage as fraction of price
        verbose: Print debug information
        
    Returns:
        DataFrame with strategy results including position, entry_price, pnl, equity
    """
    # Convert to eager mode for faster calculations
    df_eager = data.clone().with_columns([
        pl.col('close').shift(1).alias('prev_close'),
    ])
    
    n = len(df_eager)
    
    # Calculate Bollinger Bands using the full price series
    close_prices = df_eager['close'].to_numpy()
    sma, upper_band, lower_band = calculate_bollinger_bands(
        close_prices, window=window, num_std=std_multiplier
    )
    
    # Calculate z-scores
    std = pd.Series(close_prices).rolling(window=window).std().values
    std = np.where(np.isnan(std), 0, std)
    zscores = np.where(std == 0, 0, (close_prices - sma) / std)
    
    # Add signals to DataFrame
    df_eager = df_eager.with_columns([
        pl.Series('sma', sma),
        pl.Series('upper_band', upper_band),
        pl.Series('lower_band', lower_band),
        pl.Series('zscores', zscores),
    ])
    
    # Generate signals
    signals = np.zeros(n, dtype=np.int32)
    for i in range(window + 1, n):
        zscore = zscores[i]
        if zscore < min_zscore:
            signals[i] = 1  # Long signal
        elif zscore > max_zscore:
            signals[i] = -1  # Short signal
    
    df_eager = df_eager.with_columns([
        pl.Series('signal', signals),
    ])
    
    # Run the strategy
    positions = np.zeros(n, dtype=np.float64)
    entry_prices = np.zeros(n, dtype=np.float64)
    entry_times = np.zeros(n, dtype=np.float64)
    pnl = np.zeros(n, dtype=np.float64)
    
    position = 0.0  # Use float for fractional Bitcoin units
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
                position = position_value / entry_price  # Fractional units
                if position * entry_price > capital:
                    position = capital / entry_price
                entry_time = i
                if verbose:
                    print(
                        f"   Entry LONG at i={i}, price={current_price:.2f}, "
                        f"entry_price={entry_price:.2f}, position={position:.6f} units"
                    )
            
            elif current_signal == -1:
                # Short: price far above SMA
                position_value = capital * position_size_pct
                entry_price = current_price * (1 - slippage_pct)  # Sell at lower price
                position = -(position_value / entry_price)  # Fractional units
                if abs(position) * entry_price > capital:
                    position = -(capital / entry_price)
                entry_time = i
                if verbose:
                    print(
                        f"   Entry SHORT at i={i}, price={current_price:.2f}, "
                        f"entry_price={entry_price:.2f}, position={position:.6f} units"
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
        pl.col('equity').pct_change().fill_null(0).alias('returns'),
    ])
    
    df_eager = df_eager.with_columns([
        pl.col('returns').cum_sum().alias('cumulative_returns'),
    ])
    
    return df_eager


def calculate_metrics(df: pl.DataFrame, capital: float = 10000.0) -> dict:
    """Calculate performance metrics from strategy results.
    
    Args:
        df: DataFrame with strategy results (must have: pnl, returns, equity)
        capital: Initial capital
        
    Returns:
        Dictionary with performance metrics
    """
    # Get non-zero PnL values (actual trades)
    pnl_series = df['pnl'].to_numpy()
    trade_pnl = pnl_series[pnl_series != 0]
    
    total_trades = len(trade_pnl)
    
    if total_trades == 0:
        return {
            'total_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'total_trades': 0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
        }
    
    # Total return
    final_equity = df['equity'].last()
    total_return = (final_equity - capital) / capital
    
    # Win rate
    wins = trade_pnl[trade_pnl > 0]
    losses = trade_pnl[trade_pnl < 0]
    win_rate = len(wins) / total_trades if total_trades > 0 else 0
    
    # Average win/loss
    avg_win = wins.mean() if len(wins) > 0 else 0
    avg_loss = losses.mean() if len(losses) > 0 else 0
    
    # Profit factor
    total_wins = wins.sum() if len(wins) > 0 else 0
    total_losses = abs(losses.sum()) if len(losses) > 0 else 0
    profit_factor = total_wins / total_losses if total_losses > 0 else 0
    
    # Sharpe ratio (using daily returns)
    returns_series = df['returns'].to_numpy()
    non_zero_returns = returns_series[returns_series != 0]
    
    if len(non_zero_returns) > 1:
        mean_return = non_zero_returns.mean()
        std_return = non_zero_returns.std(ddof=1)
        sharpe_ratio = (mean_return / std_return) * np.sqrt(365) if std_return > 0 else 0
    else:
        sharpe_ratio = 0.0
    
    # Max drawdown
    equity_series = df['equity'].to_numpy()
    running_max = np.maximum.accumulate(equity_series)
    drawdown = (running_max - equity_series) / running_max
    max_drawdown = drawdown.max()
    
    return {
        'total_return': float(total_return),
        'sharpe_ratio': float(sharpe_ratio),
        'max_drawdown': float(max_drawdown),
        'win_rate': float(win_rate),
        'profit_factor': float(profit_factor),
        'total_trades': int(total_trades),
        'avg_win': float(avg_win),
        'avg_loss': float(avg_loss),
    }
