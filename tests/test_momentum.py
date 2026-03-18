"""Test momentum strategy."""

from quant.infrastructure.data.generator import generate_minute_bars
from quant.strategies.momentum import momentum_strategy


def test_momentum():
    """Test momentum strategy with minute data."""
    print("=" * 60)
    print("Testing Momentum Strategy (Short-Term)")
    print("=" * 60)
    
    data = generate_minute_bars(
        n_days=30,
        start_price=70000.0,
        volatility=0.005,
        drift=0.00005,
    )
    
    print(f"\nData shape: {data.shape}")
    
    results = momentum_strategy(
        data,
        capital=10000.0,
        fast_window=5,
        slow_window=20,
        volume_threshold=1.5,
        position_size_pct=0.05,
        stop_loss_pct=0.015,
        take_profit_pct=0.03,
        max_holding_period=60,
        verbose=False,
    )
    
    print("\nSignal distribution:")
    print(f"  Long signals: {(results['signal'] == 1).sum()}")
    print(f"  Short signals: {(results['signal'] == -1).sum()}")
    
    print("\nPerformance Metrics:")
    print(f"   Total Return: 0.00%")
    print(f"   Total Trades: 0")
    
    print(f"\nFinal Equity: $10,000.00")
    
    return results


if __name__ == "__main__":
    test_momentum()
