#!/usr/bin/env python3
"""Train momentum binary strategy on 2022 data."""

import sys
sys.path.insert(0, '/Users/xingjianliu/jim/quant')

import pandas as pd
from quant.infrastructure.data import create_train_validation_pipeline
from quant.strategies.momentum_binary import momentum_binary, calculate_binary_metrics
import random

# Load 2022 data
print("=" * 70)
print("  TRAINING MOMENTUM BINARY (2022 DATA)")
print("=" * 70)

# 2022 data is in the 1-minute format, resample to 5-minute
data = pd.read_csv('/Users/xingjianliu/jim/quant/data/btc_1min_2022.csv')
data['timestamp'] = pd.to_datetime(data['timestamp'])

# Resample to 5-minute bars
data = data.set_index('timestamp')
data_5min = data.resample('5min').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
}).dropna()

# Reset index so timestamp is a column
data_5min = data_5min.reset_index()

print(f"\nLoaded {len(data_5min):,} rows (5-minute)")
print(f"Date range: {data_5min['timestamp'].min()} to {data_5min['timestamp'].max()}")

# Split into train/validation (80/20)
result = create_train_validation_pipeline(data_5min, train_ratio=0.8, verbose=True)
train_df = result['train']
val_df = result['val']

# 5-minute binary market parameters
print("\nGrid search for momentum binary params...")

fast_window_options = [3, 5, 7, 10]
slow_window_options = [10, 15, 20, 25]
momentum_threshold_options = [0.001, 0.002, 0.003, 0.005]
volume_threshold_options = [1.2, 1.3, 1.5, 1.8]
stop_loss_options = [0.01, 0.015, 0.02]
take_profit_options = [0.015, 0.02, 0.025, 0.03]
max_hold_options = [10, 15, 20, 25]

n_samples = 100
print(f"Testing {n_samples} parameter combinations...")

random.seed(42)

best_params = None
best_score = -float('inf')
best_metrics = None
results_list = []

for i in range(n_samples):
    params = {
        'fast_window': random.choice(fast_window_options),
        'slow_window': random.choice(slow_window_options),
        'momentum_threshold': random.choice(momentum_threshold_options),
        'volume_threshold': random.choice(volume_threshold_options),
        'stop_loss_pct': random.choice(stop_loss_options),
        'take_profit_pct': random.choice(take_profit_options),
        'max_holding_period': random.choice(max_hold_options),
    }

    try:
        results = momentum_binary(
            train_df.copy(),
            capital=10000.0,
            **params,
            verbose=False,
        )

        metrics = calculate_binary_metrics(results, capital=10000.0)

        # Score: Sharpe - 0.5 * drawdown
        score = metrics['sharpe_ratio'] - 0.5 * metrics['max_drawdown']

        results_list.append({
            **params,
            'total_return': metrics['total_return'],
            'sharpe_ratio': metrics['sharpe_ratio'],
            'max_drawdown': metrics['max_drawdown'],
            'win_rate': metrics['win_rate'],
            'profit_factor': metrics['profit_factor'],
            'total_trades': metrics['total_trades'],
            'score': score,
        })

        if score > best_score:
            best_score = score
            best_params = params.copy()
            best_metrics = metrics.copy()

    except Exception:
        continue

    if (i + 1) % 25 == 0:
        print(f"   {i + 1}/{n_samples}")

print(f"\n   {n_samples}/{n_samples}")

# Sort by score
results_df = pd.DataFrame(results_list)
results_df = results_df.sort_values('score', ascending=False)

print("\n" + "=" * 70)
print("   BEST PARAMETERS FOUND")
print("=" * 70)

for key, value in best_params.items():
    print(f"   {key}: {value}")

print(f"\n   Best Score: {best_score:.4f}")
print(f"\n   Performance on TRAIN set:")
print(f"     Total Return: {best_metrics['total_return']*100:+.2f}%")
print(f"     Sharpe Ratio: {best_metrics['sharpe_ratio']:.2f}")
print(f"     Max Drawdown: {best_metrics['max_drawdown']*100:+.2f}%")
print(f"     Win Rate: {best_metrics['win_rate']*100:.2f}%")
print(f"     Total Trades: {best_metrics['total_trades']}")

# Show top 15
print("\n   Top 15 parameter combinations:")
print(results_df.head(15)[['fast_window', 'slow_window', 'momentum_threshold',
                           'volume_threshold', 'stop_loss_pct', 'take_profit_pct',
                           'max_holding_period', 'score', 'sharpe_ratio', 'total_return']].to_string(index=False))

# Save results
import json
results = {
    'best_params': best_params,
    'best_score': best_score,
    'train_metrics': best_metrics,
    'total_samples': n_samples,
}
with open('/Users/xingjianliu/jim/quant/train_results/momentum_binary_2022_best.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n   Best params saved to: train_results/momentum_binary_2022_best.json")
