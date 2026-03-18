"""Rigorous train/validation/test split for backtesting.

Implements proper train/validation/test split for hyperparameter tuning:
- TRAIN: Used for hyperparameter optimization (grid search, etc.)
- VALIDATION: Single run only - no further tuning after this
- TEST: Final performance evaluation

This prevents data leakage and overfitting.
"""

from datetime import datetime

import pandas as pd
import polars as pl

from quant.infrastructure.data.real_data import generate_historical_polymarket_data
from quant.strategies.mean_reversion_polymarket import calculate_metrics, mean_reversion_polymarket


def train_validation_test_split(
    data: pd.DataFrame,
    train_ratio: float = 0.6,
    val_ratio: float = 0.2,
    test_ratio: float = 0.2,
) -> tuple:
    """
    Split data into train/validation/test sets.

    Args:
        data: DataFrame with OHLCV data
        train_ratio: Proportion for training
        val_ratio: Proportion for validation
        test_ratio: Proportion for testing

    Returns:
        Tuple of (train_df, val_df, test_df)
    """

    n = len(data)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)

    train_df = data.iloc[:train_end].copy()
    val_df = data.iloc[train_end:val_end].copy()
    test_df = data.iloc[val_end:].copy()

    return train_df, val_df, test_df


def run_train_validation_test_pipeline(
    n_days: int = 365,
    train_ratio: float = 0.6,
    val_ratio: float = 0.2,
    test_ratio: float = 0.2,
    verbose: bool = True,
) -> dict:
    """
    Run the complete train/validation/test pipeline.

    Steps:
    1. Generate historical data (2024-2025)
    2. Split into train/val/test
    3. Hyperparameter tuning on TRAIN set
    4. Single run on VALIDATION set (no further tuning)
    5. Final evaluation on TEST set

    Args:
        n_days: Total days of data
        train_ratio: Training proportion
        val_ratio: Validation proportion
        test_ratio: Test proportion
        verbose: Print progress

    Returns:
        Dictionary with all metrics
    """
    today = datetime.now()
    end_date = today.strftime("%Y-%m-%d")
    start_date = (today - pd.Timedelta(days=n_days)).strftime("%Y-%m-%d")

    if verbose:
        print(f"Generating data from {start_date} to {end_date}...")
        print(f"Today is {today.strftime('%Y-%m-%d')}")

    # Generate historical data
    data_pd = generate_historical_polymarket_data(
        market_id="BTC-01012024",
        start_date=start_date,
        end_date=end_date,
        interval_minutes=5,
    )

    # Split data
    train_df, val_df, test_df = train_validation_test_split(
        data_pd,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
    )

    if verbose:
        print("\nData split:")
        print(f"  Train:   {len(train_df)} rows ({train_ratio * 100:.1f}%)")
        print(f"  Val:     {len(val_df)} rows ({val_ratio * 100:.1f}%)")
        print(f"  Test:    {len(test_df)} rows ({test_ratio * 100:.1f}%)")

    # ==================== STEP 1: HYPERPARAMETER TUNING ON TRAIN SET ====================
    if verbose:
        print("\n" + "=" * 60)
        print("STEP 1: Hyperparameter Tuning on TRAIN Set")
        print("=" * 60)

    # Grid search for optimal parameters on training data
    best_params = None
    best_sharpe = -float("inf")

    window_options = [15, 20, 25, 30]
    std_options = [1.0, 1.5, 2.0]

    for window in window_options:
        for std_mult in std_options:
            # Convert to polars
            train_polars = pl.from_pandas(train_df)

            # Run strategy
            results = mean_reversion_polymarket(
                train_polars,
                capital=10000.0,
                window=window,
                std_multiplier=std_mult,
                min_zscore=-1.2,
                max_zscore=1.1,
                verbose=False,
            )

            metrics = calculate_metrics(results, capital=10000.0)

            if metrics["sharpe_ratio"] > best_sharpe:
                best_sharpe = metrics["sharpe_ratio"]
                best_params = {
                    "window": window,
                    "std_multiplier": std_mult,
                    "min_zscore": -1.2,
                    "max_zscore": 1.1,
                }

    if verbose:
        print("Best parameters from TRAIN set:")
        print(f"  Window: {best_params['window']}")
        print(f"  Std Mult: {best_params['std_multiplier']}")
        print(f"  Best Sharpe (on TRAIN): {best_sharpe:.2f}")

    # ==================== STEP 2: SINGLE RUN ON VALIDATION SET ====================
    if verbose:
        print("\n" + "=" * 60)
        print("STEP 2: Single Run on VALIDATION Set (NO FURTHER TUNING)")
        print("=" * 60)

    val_polars = pl.from_pandas(val_df)
    results_val = mean_reversion_polymarket(
        val_polars,
        capital=10000.0,
        window=best_params["window"],
        std_multiplier=best_params["std_multiplier"],
        min_zscore=best_params["min_zscore"],
        max_zscore=best_params["max_zscore"],
        verbose=False,
    )

    val_metrics = calculate_metrics(results_val, capital=10000.0)

    if verbose:
        print("Validation Metrics:")
        print(f"  Total Return: {val_metrics['total_return'] * 100:+.2f}%")
        print(f"  Sharpe Ratio: {val_metrics['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown: {val_metrics['max_drawdown'] * 100:+.2f}%")
        print(f"  Win Rate: {val_metrics['win_rate'] * 100:.2f}%")
        print(f"  Profit Factor: {val_metrics['profit_factor']:.2f}")

    # Decision: Go to paper trading or discard?
    # Thresholds for success (adjust based on requirements)
    min_sharpe = 2.0
    min_win_rate = 0.50
    max_drawdown = 0.10

    if (
        val_metrics["sharpe_ratio"] >= min_sharpe
        and val_metrics["win_rate"] >= min_win_rate
        and val_metrics["max_drawdown"] <= max_drawdown
    ):
        if verbose:
            print("\n✅ VALIDATION PASSED - Proceed to Paper Trading")

        # ==================== STEP 3: FINAL EVALUATION ON TEST SET ====================
        if verbose:
            print("\n" + "=" * 60)
            print("STEP 3: Final Evaluation on TEST Set")
            print("=" * 60)

        test_polars = pl.from_pandas(test_df)
        results_test = mean_reversion_polymarket(
            test_polars,
            capital=10000.0,
            window=best_params["window"],
            std_multiplier=best_params["std_multiplier"],
            min_zscore=best_params["min_zscore"],
            max_zscore=best_params["max_zscore"],
            verbose=False,
        )

        test_metrics = calculate_metrics(results_test, capital=10000.0)

        if verbose:
            print("Test Metrics:")
            print(f"  Total Return: {test_metrics['total_return'] * 100:+.2f}%")
            print(f"  Sharpe Ratio: {test_metrics['sharpe_ratio']:.2f}")
            print(f"  Max Drawdown: {test_metrics['max_drawdown'] * 100:+.2f}%")
            print(f"  Win Rate: {test_metrics['win_rate'] * 100:.2f}%")
            print(f"  Profit Factor: {test_metrics['profit_factor']:.2f}")
            print("\n✅ Strategy ready for Paper Trading")

        return {
            "best_params": best_params,
            "train_metrics": None,  # Not returned - used for tuning only
            "val_metrics": val_metrics,
            "test_metrics": test_metrics,
            "status": "PAPER_TRADING",
        }
    else:
        if verbose:
            print("\n❌ VALIDATION FAILED - Strategy Discarded")
            print(f"  Required Sharpe: >= {min_sharpe} (got {val_metrics['sharpe_ratio']:.2f})")
            print(
                f"  Required Win Rate: >= {min_win_rate * 100:.0f}% "
                f"(got {val_metrics['win_rate'] * 100:.2f}%)"  # noqa: E501
            )
            print(
                f"  Max Drawdown: <= {max_drawdown * 100:.0f}% "
                f"(got {val_metrics['max_drawdown'] * 100:+.2f}%)"  # noqa: E501
            )

        return {
            "best_params": best_params,
            "val_metrics": val_metrics,
            "status": "DISCARDED",
        }


if __name__ == "__main__":
    results = run_train_validation_test_pipeline(
        n_days=365,
        train_ratio=0.6,
        val_ratio=0.2,
        test_ratio=0.2,
        verbose=True,
    )

    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Status: {results['status']}")
    if results["status"] == "PAPER_TRADING":
        print(f"Best Params: {results['best_params']}")
        print(f"Test Metrics: {results['test_metrics']}")
