"""Test mean reversion strategy."""

from quant.infrastructure.data.generator import generate_minute_bars
from quant.strategies.mean_reversion import mean_reversion_strategy, calculate_metrics


def test_mean_reversion():
    """Test mean reversion strategy with minute data."""
    print("=" * 60)
    print("Testing Mean Reversion Strategy (Short-Term)")
    print("=" * 60)
    
    data = generate_minute_bars(
        n_days=30,
        start_price=70000.0,
        volatility=0.005,
        drift=0.00005,
    )
    print(f"\nData shape: {data.shape}")
    print(f"Price range: ${data['close'].min():,.0f} - ${data['close'].max():,.0f}")
    
    results = mean_reversion_strategy(
        data,
        capital=10000.0,
        window=20,
        std_multiplier=2.0,
        position_size_pct=0.05,
        stop_loss_pct=0.015,
        take_profit_pct=0.025,
        max_holding_period=60,
        verbose=False,
    )
    
    metrics = calculate_metrics(results, capital=10000.0)
    
    print("\nPerformance Metrics:")
    print(f"   Total Return: {metrics['total_return']*100:.2f}%")
    print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown: {metrics['max_drawdown']*100:.2f}%")
    print(f"   Win Rate: {metrics['win_rate']*100:.2f}%")
    print(f"   Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"   Total Trades: {metrics['total_trades']}")
    print(f"   Avg Win: ${metrics['avg_win']:.2f}")
    print(f"   Avg Loss: ${metrics['avg_loss']:.2f}")
    
    print(f"\nFinal Equity: ${metrics['total_return']*10000 + 10000:,.2f}")
    
    return results, metrics


if __name__ == "__main__":
    test_mean_reversion()
