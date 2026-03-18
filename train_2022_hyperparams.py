#!/usr/bin/env python3
"""Hyperparameter tuning for 2022 Bitcoin 1-minute data."""

import sys
sys.path.insert(0, '/Users/xingjianliu/jim/quant')

import pandas as pd
from quant.infrastructure.data import (
    load_bitcoin_1min_csv,
    create_train_validation_pipeline,
)
from quant.strategies.mean_reversion import mean_reversion_strategy, calculate_metrics
from quant.strategies.momentum import momentum_strategy


def tune_mean_reversion_2022():
    """Tune mean reversion strategy on 2022 data."""
    print("=" * 70)
    print("  HYPERPARAMETER TUNING: MEAN REVERSION (2022 DATA)")
    print("=" * 70)

    # Load 2022 data
    print("\n1. Loading 2022 Bitcoin data...")
    data = pd.read_csv('/Users/xingjianliu/jim/quant/data/btc_1min_2022.csv')
    data['timestamp'] = pd.to_datetime(data['timestamp'])

    print(f"   Loaded {len(data):,} rows")
    print(f"   Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")

    # Split into train/validation (80/20)
    print("\n2. Splitting data (80/20)...")
    result = create_train_validation_pipeline(data, train_ratio=0.8, verbose=True)

    train_df = result['train']
    val_df = result['val']

    # Parameter grid
    print("\n3. Grid search over hyperparameters...")

    window_options = [5, 10, 15, 20, 25]
    std_options = [1.0, 1.5, 2.0, 2.5]
    stop_options = [0.01, 0.015, 0.02]
    take_profit_options = [0.015, 0.02, 0.025, 0.03]
    max_hold_options = [30, 60, 90]

    total_combinations = (
        len(window_options) *
        len(std_options) *
        len(stop_options) *
        len(take_profit_options) *
        len(max_hold_options)
    )
    print(f"   Total combinations: {total_combinations:,}")

    # For speed, sample fewer combinations
    n_samples = 50
    print(f"   Sampling {n_samples} combinations for speed...")

    import random
    random.seed(42)

    best_params = None
    best_score = -float('inf')
    best_metrics = None
    results_list = []

    for i in range(n_samples):
        # Random sample
        params = {
            'window': random.choice(window_options),
            'std_multiplier': random.choice(std_options),
            'stop_loss_pct': random.choice(stop_options),
            'take_profit_pct': random.choice(take_profit_options),
            'max_holding_period': random.choice(max_hold_options),
        }

        try:
            # Run strategy on TRAIN data
            results = mean_reversion_strategy(
                train_df.copy(),
                capital=10000.0,
                **params,
                verbose=False,
            )

            metrics = calculate_metrics(results, capital=10000.0)

            # Score: Sharpe - 0.5 * drawdown (penalize high drawdown)
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

        except Exception as e:
            continue

        if (i + 1) % 10 == 0:
            print(f"   {i + 1}/{n_samples}", end='\r')

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
    print(f"     Profit Factor: {best_metrics['profit_factor']:.2f}")
    print(f"     Total Trades: {best_metrics['total_trades']}")

    # Show top 10 results
    print("\n   Top 10 parameter combinations:")
    print(results_df.head(10)[['window', 'std_multiplier', 'stop_loss_pct',
                                'take_profit_pct', 'max_holding_period',
                                'score', 'sharpe_ratio', 'total_return']].to_string(index=False))

    return best_params, best_score, best_metrics


def tune_momentum_2022():
    """Tune momentum strategy on 2022 data."""
    print("=" * 70)
    print("  HYPERPARAMETER TUNING: MOMENTUM (2022 DATA)")
    print("=" * 70)

    # Load 2022 data
    print("\n1. Loading 2022 Bitcoin data...")
    data = pd.read_csv('/Users/xingjianliu/jim/quant/data/btc_1min_2022.csv')
    data['timestamp'] = pd.to_datetime(data['timestamp'])

    print(f"   Loaded {len(data):,} rows")
    print(f"   Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")

    # Split into train/validation (80/20)
    print("\n2. Splitting data (80/20)...")
    result = create_train_validation_pipeline(data, train_ratio=0.8, verbose=True)

    train_df = result['train']
    val_df = result['val']

    # Parameter grid
    print("\n3. Grid search over hyperparameters...")

    fast_window_options = [3, 5, 10]
    slow_window_options = [10, 20, 30]
    volume_threshold_options = [1.2, 1.5, 2.0]
    stop_options = [0.01, 0.015, 0.02]
    take_profit_options = [0.015, 0.02, 0.025, 0.03]
    max_hold_options = [30, 60, 90]

    total_combinations = (
        len(fast_window_options) *
        len(slow_window_options) *
        len(volume_threshold_options) *
        len(stop_options) *
        len(take_profit_options) *
        len(max_hold_options)
    )
    print(f"   Total combinations: {total_combinations:,}")

    # Sample fewer combinations
    n_samples = 50
    print(f"   Sampling {n_samples} combinations for speed...")

    import random
    random.seed(42)

    best_params = None
    best_score = -float('inf')
    best_metrics = None
    results_list = []

    for i in range(n_samples):
        # Random sample
        params = {
            'fast_window': random.choice(fast_window_options),
            'slow_window': random.choice(slow_window_options),
            'volume_threshold': random.choice(volume_threshold_options),
            'stop_loss_pct': random.choice(stop_options),
            'take_profit_pct': random.choice(take_profit_options),
            'max_holding_period': random.choice(max_hold_options),
        }

        try:
            # Run strategy on TRAIN data
            results = momentum_strategy(
                train_df.copy(),
                capital=10000.0,
                **params,
                verbose=False,
            )

            metrics = calculate_metrics(results, capital=10000.0)

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

        except Exception as e:
            continue

        if (i + 1) % 10 == 0:
            print(f"   {i + 1}/{n_samples}", end='\r')

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
    print(f"     Profit Factor: {best_metrics['profit_factor']:.2f}")
    print(f"     Total Trades: {best_metrics['total_trades']}")

    # Show top 10 results
    print("\n   Top 10 parameter combinations:")
    print(results_df.head(10)[['fast_window', 'slow_window', 'volume_threshold',
                                'stop_loss_pct', 'take_profit_pct', 'max_holding_period',
                                'score', 'sharpe_ratio', 'total_return']].to_string(index=False))

    return best_params, best_score, best_metrics


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--strategy', '-s', default='mean_reversion',
                       choices=['mean_reversion', 'momentum'])

    args = parser.parse_args()

    if args.strategy == 'mean_reversion':
        best_params, best_score, best_metrics = tune_mean_reversion_2022()
    else:
        best_params, best_score, best_metrics = tune_momentum_2022()

    print("\n" + "=" * 70)
    print("  TUNING COMPLETE")
    print("=" * 70)
    print(f"\nBest Params: {best_params}")
    print(f"Best Score: {best_score:.4f}")
    print(f"Train Metrics: {best_metrics}")
