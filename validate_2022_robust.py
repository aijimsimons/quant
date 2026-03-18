#!/usr/bin/env python3
"""Validate robust 2022 best params on validation set."""

import sys
sys.path.insert(0, '/Users/xingjianliu/jim/quant')

import pandas as pd
from quant.infrastructure.data import create_train_validation_pipeline
from quant.strategies.mean_reversion import mean_reversion_strategy, calculate_metrics

# Best params from robust tuning
BEST_PARAMS = {
    'window': 40,
    'std_multiplier': 2.5,
    'stop_loss_pct': 0.015,
    'take_profit_pct': 0.02,
    'max_holding_period': 120,
}

print("=" * 70)
print("  VALIDATING ROBUST 2022 MEAN REVERSION BEST PARAMS")
print("=" * 70)

# Load 2022 data
data = pd.read_csv('/Users/xingjianliu/jim/quant/data/btc_1min_2022.csv')
data['timestamp'] = pd.to_datetime(data['timestamp'])

print(f"\nLoaded {len(data):,} rows")

# Split
result = create_train_validation_pipeline(data, train_ratio=0.8, verbose=True)
train_df = result['train']
val_df = result['val']

# Run on validation
print("\nRunning strategy on VALIDATION set with robust params...")
val_results = mean_reversion_strategy(
    val_df.copy(),
    capital=10000.0,
    **BEST_PARAMS,
    verbose=False,
)

val_metrics = calculate_metrics(val_results, capital=10000.0)

print("\n" + "=" * 70)
print("   VALIDATION METRICS")
print("=" * 70)
print(f"\n   Total Return: {val_metrics['total_return']*100:+.2f}%")
print(f"   Sharpe Ratio: {val_metrics['sharpe_ratio']:.2f}")
print(f"   Max Drawdown: {val_metrics['max_drawdown']*100:+.2f}%")
print(f"   Win Rate: {val_metrics['win_rate']*100:.2f}%")
print(f"   Total Trades: {val_metrics['total_trades']}")

# Validation thresholds (more lenient for 1-minute data)
min_sharpe = 0.0
min_win_rate = 0.45
max_drawdown = 0.25

passed = (
    val_metrics['sharpe_ratio'] >= min_sharpe and
    val_metrics['win_rate'] >= min_win_rate and
    val_metrics['max_drawdown'] <= max_drawdown
)

print("\n" + "=" * 70)
print("   VALIDATION DECISION")
print("=" * 70)

if passed:
    print("\n✅ VALIDATION PASSED!")
else:
    print("\n❌ VALIDATION FAILED")
    if val_metrics['sharpe_ratio'] < min_sharpe:
        print(f"   Sharpe too low: {val_metrics['sharpe_ratio']:.2f} < {min_sharpe}")
    if val_metrics['win_rate'] < min_win_rate:
        print(f"   Win rate too low: {val_metrics['win_rate']*100:.2f}% < {min_win_rate*100:.0f}%")
    if val_metrics['max_drawdown'] > max_drawdown:
        print(f"   Drawdown too high: {val_metrics['max_drawdown']*100:+.2f}% > {max_drawdown*100:.0f}%")

# Compare train vs validation
print("\n" + "=" * 70)
print("   TRAIN vs VALIDATION COMPARISON")
print("=" * 70)
print(f"\n{'Metric':<20} {'Train':>15} {'Val':>15}")
print("-" * 50)
print(f"{'Return':<20} {154.90:>14.2f}% {val_metrics['total_return']*100:>14.2f}%")
print(f"{'Sharpe':<20} {0.39:>14.2f} {val_metrics['sharpe_ratio']:>14.2f}")
print(f"{'Max DD':<20} {16.42:>14.2f}% {val_metrics['max_drawdown']*100:>14.2f}%")
print(f"{'Win Rate':<20} {52.68:>14.2f}% {val_metrics['win_rate']*100:>14.2f}%")

# Check for overfitting
train_return = 1.549
train_sharpe = 0.39
train_dd = 0.164

return_diff = (val_metrics['total_return'] - train_return) / abs(train_return) * 100
sharpe_diff = (val_metrics['sharpe_ratio'] - train_sharpe) / abs(train_sharpe) * 100
dd_diff = (val_metrics['max_drawdown'] - train_dd) / abs(train_dd) * 100

print(f"\n{'Diff Return':<20} {return_diff:>14.2f}%")
print(f"{'Diff Sharpe':<20} {sharpe_diff:>14.2f}%")
print(f"{'Diff Max DD':<20} {dd_diff:>14.2f}%")

if abs(return_diff) < 50 and abs(sharpe_diff) < 50:
    print("\n✅ Reasonable generalization (not严重 overfitting)")
else:
    print("\n⚠️  Significant performance drop - strategy may be overfit")

print("\n" + "=" * 70)
print("  VALIDATION COMPLETE")
print("=" * 70)

# Save validation results
import json
results = {
    'best_params': BEST_PARAMS,
    'train_metrics': {
        'total_return': 1.549,
        'sharpe_ratio': 0.39,
        'max_drawdown': 0.1642,
        'win_rate': 0.5268,
    },
    'val_metrics': val_metrics,
    'status': 'PAPER_TRADING' if passed else 'REVIEW_NEEDED',
}
with open('/Users/xingjianliu/jim/quant/train_results/mean_reversion_2022_robust_val.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to: train_results/mean_reversion_2022_robust_val.json")
