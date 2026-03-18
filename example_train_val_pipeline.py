#!/usr/bin/env python3
"""
Example: Using the infrastructure for train/validation backtesting pipeline.

This shows how to:
1. Load 1-minute Bitcoin data
2. Split into train/validation chronologically
3. Run hyperparameter tuning on TRAIN
4. Validate on VALIDATION (single run, no further tuning)
"""

import sys
sys.path.insert(0, '/Users/xingjianliu/jim/quant')

import pandas as pd
from quant.infrastructure.data import (
    load_bitcoin_1min_csv,
    create_train_validation_pipeline,
)

from quant.strategies.mean_reversion import mean_reversion_strategy, calculate_metrics


def train_validation_pipeline_example():
    """Run a complete train/validation pipeline."""

    print("=" * 70)
    print("  TRAIN/VALIDATION PIPELINE EXAMPLE")
    print("=" * 70)

    # ==================== STEP 1: LOAD DATA ====================
    print("\n1. Loading 1-minute Bitcoin data...")
    data = load_bitcoin_1min_csv()
    print(f"   Loaded {len(data):,} rows")
    print(f"   Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")

    # ==================== STEP 2: SPLIT DATA ====================
    print("\n2. Splitting data chronologically (80/20)...")
    result = create_train_validation_pipeline(data, train_ratio=0.8, verbose=True)

    train_df = result['train']
    val_df = result['val']

    # ==================== STEP 3: HYPERPARAMETER TUNING ON TRAIN ====================
    print("\n" + "=" * 70)
    print("3. HYPERPARAMETER TUNING ON TRAIN SET")
    print("=" * 70)

    # Parameter grid
    window_options = [10, 20, 30]
    std_options = [1.5, 2.0, 2.5]

    best_params = None
    best_sharpe = -float('inf')
    best_metrics = None

    print(f"\nTesting {len(window_options) * len(std_options)} parameter combinations...")

    for window in window_options:
        for std_mult in std_options:
            try:
                # Run strategy on TRAIN data
                results = mean_reversion_strategy(
                    train_df.copy(),
                    capital=10000.0,
                    window=window,
                    std_multiplier=std_mult,
                    position_size_pct=0.05,
                    stop_loss_pct=0.02,
                    take_profit_pct=0.025,
                    max_holding_period=60,
                    verbose=False,
                )

                metrics = calculate_metrics(results, capital=10000.0)

                if metrics['sharpe_ratio'] > best_sharpe:
                    best_sharpe = metrics['sharpe_ratio']
                    best_params = {
                        'window': window,
                        'std_multiplier': std_mult,
                    }
                    best_metrics = metrics.copy()

            except Exception as e:
                continue

    print(f"\nBest parameters from TRAIN set:")
    print(f"  Window: {best_params['window']}")
    print(f"  Std Mult: {best_params['std_multiplier']}")
    print(f"  Best Sharpe (on TRAIN): {best_sharpe:.2f}")

    # ==================== STEP 4: VALIDATION (SINGLE RUN) ====================
    print("\n" + "=" * 70)
    print("4. VALIDATION - Single run with best params (NO FURTHER TUNING)")
    print("=" * 70)

    val_results = mean_reversion_strategy(
        val_df.copy(),
        capital=10000.0,
        window=best_params['window'],
        std_multiplier=best_params['std_multiplier'],
        position_size_pct=0.05,
        stop_loss_pct=0.02,
        take_profit_pct=0.025,
        max_holding_period=60,
        verbose=False,
    )

    val_metrics = calculate_metrics(val_results, capital=10000.0)

    print(f"\nValidation Metrics:")
    print(f"  Total Return: {val_metrics['total_return']*100:+.2f}%")
    print(f"  Sharpe Ratio: {val_metrics['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown: {val_metrics['max_drawdown']*100:+.2f}%")
    print(f"  Win Rate: {val_metrics['win_rate']*100:.2f}%")

    # ==================== STEP 5: DECISION ====================
    print("\n" + "=" * 70)
    print("5. VALIDATION DECISION")
    print("=" * 70)

    # Validation thresholds
    min_sharpe = 0.5
    min_win_rate = 0.50
    max_drawdown = 0.10

    passed = (
        val_metrics['sharpe_ratio'] >= min_sharpe and
        val_metrics['win_rate'] >= min_win_rate and
        val_metrics['max_drawdown'] <= max_drawdown
    )

    if passed:
        print("\n✅ VALIDATION PASSED - Strategy ready for paper trading!")
        print(f"   (Required Sharpe >= {min_sharpe}, got {val_metrics['sharpe_ratio']:.2f})")
        print(f"   (Required Win Rate >= {min_win_rate*100:.0f}%, got {val_metrics['win_rate']*100:.2f}%)")
        print(f"   (Required Max DD <= {max_drawdown*100:.0f}%, got {val_metrics['max_drawdown']*100:+.2f}%)")
    else:
        print("\n❌ VALIDATION FAILED - Strategy discarded")
        if val_metrics['sharpe_ratio'] < min_sharpe:
            print(f"   Sharpe too low: {val_metrics['sharpe_ratio']:.2f} < {min_sharpe}")
        if val_metrics['win_rate'] < min_win_rate:
            print(f"   Win rate too low: {val_metrics['win_rate']*100:.2f}% < {min_win_rate*100:.0f}%")
        if val_metrics['max_drawdown'] > max_drawdown:
            print(f"   Drawdown too high: {val_metrics['max_drawdown']*100:+.2f}% > {max_drawdown*100:.0f}%")

    return passed, best_params, val_metrics


if __name__ == "__main__":
    passed, best_params, val_metrics = train_validation_pipeline_example()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Status: {'✅ PASS' if passed else '❌ FAIL'}")
    print(f"Best Params: {best_params}")
    print(f"Validation Metrics: {val_metrics}")
