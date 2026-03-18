#!/usr/bin/env python3
"""Validate 2022 best params on 2026 data."""

import sys
sys.path.insert(0, '/Users/xingjianliu/jim/quant')

import pandas as pd
from quant.infrastructure.data import create_train_validation_pipeline
from quant.strategies.mean_reversion import mean_reversion_strategy, calculate_metrics

# Best params from 2022
BEST_PARAMS = {
    'window': 40,
    'std_multiplier': 2.5,
    'stop_loss_pct': 0.015,
    'take_profit_pct': 0.02,
    'max_holding_period': 120,
}

print("=" * 70)
print("  VALIDATING 2022 BEST PARAMS ON 2026 DATA")
print("=" * 70)

# Load 2026 data
data = pd.read_csv('/Users/xingjianliu/jim/quant/data/btc_1min_2026.csv')
data['timestamp'] = pd.to_datetime(data['timestamp'])

print(f"\nLoaded {len(data):,} rows")
print(f"Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")

# Split into train/validation (80/20)
result = create_train_validation_pipeline(data, train_ratio=0.8, verbose=True)
train_df = result['train']
val_df = result['val']

# Run on 2026 validation
print("\nRunning 2022-tuned strategy on 2026 VALIDATION set...")
val_results = mean_reversion_strategy(
    val_df.copy(),
    capital=10000.0,
    **BEST_PARAMS,
    verbose=False,
)

val_metrics = calculate_metrics(val_results, capital=10000.0)

# Also run on 2026 train to see training performance
print("\nRunning on 2026 TRAIN set for comparison...")
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
print("   2022 PARAMS ON 2026 DATA - COMPARISON")
print("=" * 70)
print(f"\n{'Metric':<20} {'2022 Train':>15} {'2022 Val':>15} {'2026 Val':>15}")
print("-" * 65)
print(f"{'Return':<20} {154.90:>14.2f}% {21.24:>14.2f}% {val_metrics['total_return']*100:>14.2f}%")
print(f"{'Sharpe':<20} {0.39:>14.2f} {0.53:>14.2f} {val_metrics['sharpe_ratio']:>14.2f}")
print(f"{'Max DD':<20} {16.42:>14.2f}% {5.65:>14.2f}% {val_metrics['max_drawdown']*100:>14.2f}%")
print(f"{'Win Rate':<20} {52.68:>14.2f}% {55.58:>14.2f}% {val_metrics['win_rate']*100:>14.2f}%")

print("\n" + "=" * 70)
print("   STRATEGY GENERALIZATION ANALYSIS")
print("=" * 70)

# Check if strategy generalizes
if val_metrics['total_return'] > 0:
    print("\n✅ Strategy makes money on 2026 data!")
elif val_metrics['total_return'] < -0.10:
    print("\n❌ Strategy loses money on 2026 data")
else:
    print("\n⚠️  Strategy is flat on 2026 data")

if val_metrics['sharpe_ratio'] > 0:
    print("✅ Strategy has positive Sharpe ratio on 2026 data")
else:
    print("❌ Strategy has negative Sharpe ratio on 2026 data")

if val_metrics['max_drawdown'] < 0.10:
    print("✅ Drawdown is manageable (<10%)")
else:
    print(f"⚠️  Drawdown is high: {val_metrics['max_drawdown']*100:.2f}%")

print("\n" + "=" * 70)
print("  VALIDATION COMPLETE")
print("=" * 70)

# Save results
import json
results = {
    'best_params_from_2022': BEST_PARAMS,
    '2022_train_metrics': {
        'total_return': 1.549,
        'sharpe_ratio': 0.39,
        'max_drawdown': 0.1642,
        'win_rate': 0.5268,
    },
    '2022_val_metrics': {
        'total_return': 0.2124,
        'sharpe_ratio': 0.53,
        'max_drawdown': 0.0565,
        'win_rate': 0.5558,
    },
    '2026_val_metrics': val_metrics,
}
with open('/Users/xingjianliu/jim/quant/train_results/mean_reversion_2022_on_2026.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to: train_results/mean_reversion_2022_on_2026.json")
