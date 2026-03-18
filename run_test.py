"""Quick test of mean reversion strategy."""

import sys
import os

# Add the project root to path
project_root = '/Users/xingjianliu/jim/quant'
sys.path.insert(0, project_root)

# Import directly from files
from strategies.mean_reversion import mean_reversion_strategy, calculate_metrics
from infrastructure.data.generator import generate_minute_bars

print("Import test passed!")

data = generate_minute_bars(n_days=5)
print(f"Generated {len(data)} rows of data")

results = mean_reversion_strategy(data, capital=10000.0)
metrics = calculate_metrics(results, capital=10000.0)

print(f"\nPerformance Metrics:")
print(f"  Total Return: {metrics['total_return']*100:.2f}%")
print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"  Max Drawdown: {metrics['max_drawdown']*100:.2f}%")
print(f"  Win Rate: {metrics['win_rate']*100:.2f}%")
print(f"  Total Trades: {metrics['total_trades']}")
print(f"  Final Equity: ${metrics['total_return']*10000 + 10000:,.2f}")
