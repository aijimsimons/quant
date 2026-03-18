"""Walk-forward validation for Bitcoin mean reversion backtesting.

Uses aggressive parameters to generate enough trades for statistical significance.
"""

import pandas as pd
from datetime import datetime
import polars as pl

from quant.infrastructure.data.real_data import load_bitcoin_ohlcv_csv
from quant.strategies.mean_reversion_bitcoin import mean_reversion_bitcoin, calculate_metrics


def run_walk_forward_validation(
    window_size: int = 100,
    train_ratio: float = 0.7,
    test_size: int = 73,
    verbose: bool = True,
) -> dict:
    """
    Run walk-forward validation on Bitcoin data.
    
    Args:
        window_size: Size of each rolling window
        train_ratio: Proportion used for training within each window
        test_size: Size of final hold-out test period
        verbose: Print progress
        
    Returns:
        Dictionary with all metrics and status
    """
    today = datetime.now()
    
    if verbose:
        print("=" * 60)
        print("WALK-FORWARD VALIDATION FOR BITCOIN MEAN REVERSION")
        print("=" * 60)
    
    # ==================== STEP 0: LOAD REAL BITCOIN DATA ====================
    btc_df = load_bitcoin_ohlcv_csv()
    
    if verbose:
        print(f"\nLoaded {len(btc_df)} rows")
    
    # ==================== STEP 1: WALK-FORWARD VALIDATION ====================
    if verbose:
        print("\nRunning walk-forward validation...")
    
    n = len(btc_df)
    num_windows = n - window_size - test_size + 1
    
    # Aggressive parameter grid (more trades = better statistics)
    window_options = [3, 5, 7]
    std_options = [0.8, 1.0, 1.2]
    zscore_options = [(-0.5, 0.5), (-0.6, 0.6), (-0.8, 0.8)]
    stop_loss_options = [0.005, 0.01]
    take_profit_options = [0.01, 0.02]
    
    best_params = None
    best_avg_sharpe = -float('inf')
    param_count = 0
    
    for window in window_options:
        for std_mult in std_options:
            for min_z, max_z in zscore_options:
                for stop_loss in stop_loss_options:
                    for take_profit in take_profit_options:
                        param_count += 1
                        window_sharpe_scores = []
                        
                        # Sample fewer windows for speed (every 3rd window)
                        for i in range(0, num_windows, 3):
                            window_data = btc_df.iloc[i:i+window_size].copy()
                            data_polars = pl.from_pandas(window_data)
                            
                            try:
                                results = mean_reversion_bitcoin(
                                    data_polars,
                                    capital=10000.0,
                                    window=window,
                                    std_multiplier=std_mult,
                                    min_zscore=min_z,
                                    max_zscore=max_z,
                                    stop_loss_pct=stop_loss,
                                    take_profit_pct=take_profit,
                                    verbose=False,
                                )
                                
                                train_end = int(window_size * train_ratio)
                                val_df = results.select(pl.all().slice(train_end, window_size - train_end))
                                val_metrics = calculate_metrics(val_df, capital=10000.0)
                                
                                # Count if we have enough trades (at least 5)
                                if val_metrics['total_trades'] >= 5:
                                    window_sharpe_scores.append(val_metrics['sharpe_ratio'])
                            except Exception:
                                continue
                        
                        if window_sharpe_scores:
                            avg_sharpe = sum(window_sharpe_scores) / len(window_sharpe_scores)
                            
                            if avg_sharpe > best_avg_sharpe:
                                best_avg_sharpe = avg_sharpe
                                best_params = {
                                    'window': window,
                                    'std_multiplier': std_mult,
                                    'min_zscore': min_z,
                                    'max_zscore': max_z,
                                    'stop_loss_pct': stop_loss,
                                    'take_profit_pct': take_profit,
                                }
    
    if verbose:
        print(f"   Tested {param_count} parameter combinations")
        print(f"   Best Avg Sharpe: {best_avg_sharpe:.2f}")
        print(f"   Best Params: {best_params}")
    
    # ==================== STEP 2: FINAL VALIDATION ====================
    data_polars = pl.from_pandas(btc_df)
    results = mean_reversion_bitcoin(
        data_polars,
        capital=10000.0,
        window=best_params['window'],
        std_multiplier=best_params['std_multiplier'],
        min_zscore=best_params['min_zscore'],
        max_zscore=best_params['max_zscore'],
        stop_loss_pct=best_params['stop_loss_pct'],
        take_profit_pct=best_params['take_profit_pct'],
        verbose=False,
    )
    
    # Extract periods
    val_start = n - test_size - window_size
    val_end = n - test_size
    
    val_df = results.select(pl.all().slice(val_start, window_size))
    val_metrics = calculate_metrics(val_df, capital=10000.0)
    
    test_df = results.select(pl.all().slice(n - test_size, test_size))
    test_metrics = calculate_metrics(test_df, capital=10000.0)
    
    train_df = results.select(pl.all().slice(0, val_start))
    train_metrics = calculate_metrics(train_df, capital=10000.0)
    
    # ==================== STEP 3: VALIDATION DECISION ====================
    val_passed = (
        val_metrics['sharpe_ratio'] >= 0.5 and
        val_metrics['win_rate'] >= 0.50 and
        val_metrics['max_drawdown'] <= 0.10
    )
    
    if verbose:
        print(f"\nValidation Sharpe: {val_metrics['sharpe_ratio']:.2f}")
        print(f"Validation Win Rate: {val_metrics['win_rate']*100:.2f}%")
        print(f"Validation Max Drawdown: {val_metrics['max_drawdown']*100:+.2f}%")
        print(f"\n{'✅ PASSED' if val_passed else '❌ FAILED'}")
    
    return {
        'best_params': best_params,
        'train_metrics': train_metrics,
        'val_metrics': val_metrics,
        'test_metrics': test_metrics,
        'status': 'PAPER_TRADING' if val_passed else 'DISCARDED',
    }


if __name__ == "__main__":
    results = run_walk_forward_validation(verbose=True)
