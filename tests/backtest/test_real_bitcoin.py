"""Test mean reversion on real Bitcoin data."""

import sys
sys.path.insert(0, '/Users/xingjianliu/jim/quant')

from quant.infrastructure.data.real_data import load_bitcoin_ohlcv_csv
from quant.strategies.mean_reversion_bitcoin import mean_reversion_bitcoin, calculate_metrics
import polars as pl


def test_real_bitcoin_backtest():
    """Test strategy on real Bitcoin OHLCV data."""
    print("=" * 60)
    print("Testing Mean Reversion on REAL Bitcoin Data")
    print("=" * 60)
    
    # Load real Bitcoin data
    print("\n1. Loading real Bitcoin OHLCV data from CoinGecko API...")
    btc_df = load_bitcoin_ohlcv_csv()
    print(f"   Loaded {len(btc_df)} rows")
    print(f"   Date range: {btc_df['timestamp'].min()} to {btc_df['timestamp'].max()}")
    print(f"   Price range: ${btc_df['close'].min():,.2f} to ${btc_df['close'].max():,.2f}")
    
    # Convert to Polars
    data = pl.from_pandas(btc_df)
    
    # Run mean reversion strategy on real Bitcoin data
    print("\n2. Running mean reversion strategy on REAL Bitcoin data...")
    results = mean_reversion_bitcoin(
        data,
        capital=10000.0,
        window=20,
        std_multiplier=2.0,
        position_size_pct=0.05,
        stop_loss_pct=0.02,
        take_profit_pct=0.03,
        max_holding_period=20,
        min_zscore=-2.0,
        max_zscore=2.0,
        slippage_pct=0.001,
        verbose=False,
    )
    
    # Calculate metrics
    metrics = calculate_metrics(results, capital=10000.0)
    
    print("\n3. Performance Metrics:")
    print(f"   Total Return:     {metrics['total_return']*100:+.2f}%")
    print(f"   Sharpe Ratio:     {metrics['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown:     {metrics['max_drawdown']*100:+.2f}%")
    print(f"   Win Rate:         {metrics['win_rate']*100:.2f}%")
    print(f"   Profit Factor:    {metrics['profit_factor']:.2f}")
    print(f"   Total Trades:     {metrics['total_trades']}")
    print(f"   Avg Win:          ${metrics['avg_win']:.2f}")
    print(f"   Avg Loss:         ${metrics['avg_loss']:.2f}")
    print(f"   Final Equity:     ${metrics['total_return']*10000 + 10000:,.2f}")
    
    return metrics


if __name__ == "__main__":
    metrics = test_real_bitcoin_backtest()
