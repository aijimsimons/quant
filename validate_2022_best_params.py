#!/usr/bin/env python3
"""Validate 2022 best hyperparameters on validation set."""

import sys
sys.path.insert(0, '/Users/xingjianliu/jim/quant')

import pandas as pd
from quant.infrastructure.data import (
    create_train_validation_pipeline,
)
from quant.strategies.mean_reversion import mean_reversion_strategy, calculate_metrics

# Best params from training
BEST_PARAMS = {
    'window': 25,
    'std_multiplier': 2.5,
    'stop_loss_pct': 0.01,
    'take_profit_pct': 0.03,
    'max_holding_period': 90,
}

print("=" * 70)
print("  VALIDATING 2022 MEAN REVERSION BEST PARAMS")
print("=" * 70)

# Load 2022 data
print("\n1. Loading 2022 Bitcoin data...")
data = pd.read_csv('/Users/xingjianliu/jim/quant/data/btc_1min_2022.csv')
data['timestamp'] = pd.to_datetime(data['timestamp'])

print(f"   Loaded {len(data):,} rows")
print(f"   Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")

# Split into train/validation
print("\n2. Splitting data (80/20)...")
result = create_train_validation_pipeline(data, train_ratio=0.8, verbose=True)

train_df = result['train']
val_df = result['val']

print("\n3. Running strategy on VALIDATION set with best params...")
print(f"   Params: {BEST_PARAMS}")

# Run strategy on VALIDATION data
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
print(f"   Profit Factor: {val_metrics['profit_factor']:.2f}")
print(f"   Total Trades: {val_metrics['total_trades']}")

# Validation thresholds
min_sharpe = 0.5
min_win_rate = 0.50
max_drawdown = 0.10

print("\n" + "=" * 70)
print("   VALIDATION DECISION")
print("=" * 70)

passed = (
    val_metrics['sharpe_ratio'] >= min_sharpe and
    val_metrics['win_rate'] >= min_win_rate and
    val_metrics['max_drawdown'] <= max_drawdown
)

if passed:
    print("\n✅ VALIDATION PASSED - Strategy ready for paper trading!")
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
print(f"{'Return':<20} {116.37:>14.2f}% {val_metrics['total_return']*100:>14.2f}%")
print(f"{'Sharpe':<20} {0.32:>14.2f} {val_metrics['sharpe_ratio']:>14.2f}")
print(f"{'Max DD':<20} {23.21:>14.2f}% {val_metrics['max_drawdown']*100:>14.2f}%")
print(f"{'Win Rate':<20} {47.43:>14.2f}% {val_metrics['win_rate']*100:>14.2f}%")

# Check for overfitting (train significantly better than validation)
train_return = 1.1637
train_sharpe = 0.319
train_dd = 0.232

return_diff = (val_metrics['total_return'] - train_return) / abs(train_return) * 100
sharpe_diff = (val_metrics['sharpe_ratio'] - train_sharpe) / abs(train_sharpe) * 100
dd_diff = (val_metrics['max_drawdown'] - train_dd) / abs(train_dd) * 100

print(f"\n{'Diff Return':<20} {return_diff:>14.2f}%")
print(f"{'Diff Sharpe':<20} {sharpe_diff:>14.2f}%")
print(f"{'Diff Max DD':<20} {dd_diff:>14.2f}%")

print("\n" + "=" * 70)
print("  VALIDATION COMPLETE")
print("=" * 70)
