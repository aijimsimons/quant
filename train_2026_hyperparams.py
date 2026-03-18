#!/usr/bin/env python3
"""Hyperparameter tuning for 2026 Bitcoin 1-minute data."""

import sys
sys.path.insert(0, '/Users/xingjianliu/jim/quant')

import pandas as pd
from quant.infrastructure.data import create_train_validation_pipeline
from quant.strategies.mean_reversion import mean_reversion_strategy, calculate_metrics
import random

# Load 2026 data
print("=" * 70)
print("  HYPERPARAMETER TUNING: 2026 MEAN REVERSION")
print("=" * 70)

data = pd.read_csv('/Users/xingjianliu/jim/quant/data/btc_1min_2026.csv')
data['timestamp'] = pd.to_datetime(data['timestamp'])

print(f"\nLoaded {len(data):,} rows")
print(f"Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")

# Split
result = create_train_validation_pipeline(data, train_ratio=0.8, verbose=True)
train_df = result['train']
val_df = result['val']

# 2026-specific parameters (tighter windows, more aggressive stops)
print("\nGrid search with 2026 parameters...")

# 2026-specific parameters
window_options = [10, 15, 20, 25, 30]  # Tighter windows for consolidation
std_options = [1.0, 1.5, 2.0]          # Tighter bands
stop_options = [0.008, 0.01, 0.012]    # Tighter stops (consolidation)
take_profit_options = [0.01, 0.015, 0.02]  # Tighter takes
max_hold_options = [20, 40, 60, 80]     # Shorter holds

n_samples = 100
print(f"Testing {n_samples} parameter combinations...")

random.seed(42)

best_params = None
best_score = -float('inf')
best_metrics = None
results_list = []

for i in range(n_samples):
    params = {
        'window': random.choice(window_options),
        'std_multiplier': random.choice(std_options),
        'stop_loss_pct': random.choice(stop_options),
        'take_profit_pct': random.choice(take_profit_options),
        'max_holding_period': random.choice(max_hold_options),
    }

    try:
        results = mean_reversion_strategy(
            train_df.copy(),
            capital=10000.0,
            **params,
            verbose=False,
        )

        metrics = calculate_metrics(results, capital=10000.0)

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
print("   BEST PARAMETERS FOUND (2026)")
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
print(results_df.head(15)[['window', 'std_multiplier', 'stop_loss_pct',
                           'take_profit_pct', 'max_holding_period',
                           'score', 'sharpe_ratio', 'total_return']].to_string(index=False))

# Save results
import json
results = {
    'best_params': best_params,
    'best_score': best_score,
    'train_metrics': best_metrics,
    'total_samples': n_samples,
}
with open('/Users/xingjianliu/jim/quant/train_results/mean_reversion_2026_best.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n   Best params saved to: train_results/mean_reversion_2026_best.json")
