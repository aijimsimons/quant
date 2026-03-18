"""Rigorous backtest with train/validation/test split."""

import sys

sys.path.insert(0, '/Users/xingjianliu/jim/quant')

from tests.backtest.train_val_test_split import run_train_validation_test_pipeline

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
    if results['status'] == 'PAPER_TRADING':
        print(f"Best Params: {results['best_params']}")
        print(f"Test Metrics: {results['test_metrics']}")
