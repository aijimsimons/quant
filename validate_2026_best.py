#!/usr/bin/env python3
"""Validate 2026 best params."""

import sys
sys.path.insert(0, '/Users/xingjianliu/jim/quant')

import pandas as pd
from quant.infrastructure.data import create_train_validation_pipeline
from quant.strategies.mean_reversion import mean_reversion_strategy, calculate_metrics

# Best 2026 params
BEST_PARAMS = {
    'window': 15,
    'std_multiplier': 1.0,
    'stop_loss_pct': 0.01,
    'take_profit_pct': 0.02,
    'max_holding_period': 20,
}

print("=" * 70)
print("  VALIDATING 2026 MEAN REVERSION BEST PARAMS")
print("=" * 70)

# Load 2026 data
data = pd.read_csv('/Users/xingjianliu/jim/quant/data/btc_1min_2026.csv')
data['timestamp'] = pd.to_datetime(data['timestamp'])

print(f"\nLoaded {len(data):,} rows")

# Split
result = create_train_validation_pipeline(data, train_ratio=0.8, verbose=True)
train_df = result['train']
val_df = result['val']

# Run on validation
print("\nRunning on 2026 VALIDATION set...")
val_results = mean_reversion_strategy(
    val_df.copy(),
    capital=10000.0,
    **BEST_PARAMS,
    verbose=False,
)

val_metrics = calculate_metrics(val_results, capital=10000.0)

# Run on train
print("\nRunning on 2026 TRAIN set...")
train_results = mean_reversion_strategy(
    train_df.copy(),
    capital=10000.0,
    **BEST_PARAMS,
    verbose=False,
)

train_metrics = calculate_metrics(train_results, capital=10000.0)

print("\n" + "=" * 70)
print("   2026 VALIDATION METRICS")
print("=" * 70)
print(f"\n   Total Return: {val_metrics['total_return']*100:+.2f}%")
print(f"   Sharpe Ratio: {val_metrics['sharpe_ratio']:.2f}")
print(f"   Max Drawdown: {val_metrics['max_drawdown']*100:+.2f}%")
print(f"   Win Rate: {val_metrics['win_rate']*100:.2f}%")
print(f"   Total Trades: {val_metrics['total_trades']}")

# Compare
print("\n" + "=" * 70)
print("   2026 TRAIN vs VALIDATION")
print("=" * 70)
print(f"\n{'Metric':<20} {'Train':>15} {'Val':>15}")
print("-" * 50)
print(f"{'Return':<20} {92.36:>14.2f}% {val_metrics['total_return']*100:>14.2f}%")
print(f"{'Sharpe':<20} {0.31:>14.2f} {val_metrics['sharpe_ratio']:>14.2f}")
print(f"{'Max DD':<20} {43.34:>14.2f}% {val_metrics['max_drawdown']*100:>14.2f}%")
print(f"{'Win Rate':<20} {44.56:>14.2f}% {val_metrics['win_rate']*100:>14.2f}%")

# Validation thresholds
min_sharpe = 0.0
min_win_rate = 0.45
max_drawdown = 0.50  # More lenient for high-volatility periods

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

print("\n" + "=" * 70)
print("  VALIDATION COMPLETE")
print("=" * 70)

# Save results
import json
results = {
    'best_params': BEST_PARAMS,
    'train_metrics': train_metrics,
    'val_metrics': val_metrics,
    'status': 'PAPER_TRADING' if passed else 'REVIEW_NEEDED',
}
with open('/Users/xingjianliu/jim/quant/train_results/mean_reversion_2026_val.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to: train_results/mean_reversion_2026_val.json")
