"""Iterative backtest optimization."""

from quant.strategies.mean_reversion_polymarket import mean_reversion_polymarket, calculate_metrics
from quant.infrastructure.simulation import generate_polymarket_price_data
import polars as pl
import numpy as np


def grid_search_zscores():
    """Find optimal z-score thresholds."""
    data_pd = generate_polymarket_price_data(
        market_id="grid_search",
        n_days=30,
        start_price=50.0,
        volatility=0.8,
        interval_minutes=5,
    )
    data = pl.from_pandas(data_pd)
    
    results = []
    
    for min_z in np.arange(-1.2, -0.5, 0.1):
        for max_z in np.arange(0.5, 1.2, 0.1):
            results_df = mean_reversion_polymarket(
                data,
                capital=10000.0,
                window=20,
                std_multiplier=1.5,
                min_zscore=min_z,
                max_zscore=max_z,
                verbose=False,
            )
            metrics = calculate_metrics(results_df, capital=10000.0)
            results.append({
                "min_zscore": min_z,
                "max_zscore": max_z,
                "total_return": metrics["total_return"],
                "sharpe_ratio": metrics["sharpe_ratio"],
                "win_rate": metrics["win_rate"],
                "max_drawdown": metrics["max_drawdown"],
            })
    
    return pl.DataFrame(results)


def grid_search_windows():
    """Find optimal window size."""
    data_pd = generate_polymarket_price_data(
        market_id="window_search",
        n_days=30,
        start_price=50.0,
        volatility=0.8,
        interval_minutes=5,
    )
    data = pl.from_pandas(data_pd)
    
    results = []
    
    for window in [10, 15, 20, 25, 30]:
        results_df = mean_reversion_polymarket(
            data,
            capital=10000.0,
            window=window,
            std_multiplier=1.5,
            min_zscore=-0.8,
            max_zscore=0.8,
            verbose=False,
        )
        metrics = calculate_metrics(results_df, capital=10000.0)
        results.append({
            "window": window,
            "total_return": metrics["total_return"],
            "sharpe_ratio": metrics["sharpe_ratio"],
            "win_rate": metrics["win_rate"],
            "max_drawdown": metrics["max_drawdown"],
        })
    
    return pl.DataFrame(results)


def grid_search_std():
    """Find optimal std multiplier."""
    data_pd = generate_polymarket_price_data(
        market_id="std_search",
        n_days=30,
        start_price=50.0,
        volatility=0.8,
        interval_minutes=5,
    )
    data = pl.from_pandas(data_pd)
    
    results = []
    
    for std_mult in np.arange(1.0, 2.5, 0.25):
        results_df = mean_reversion_polymarket(
            data,
            capital=10000.0,
            window=20,
            std_multiplier=std_mult,
            min_zscore=-0.8,
            max_zscore=0.8,
            verbose=False,
        )
        metrics = calculate_metrics(results_df, capital=10000.0)
        results.append({
            "std_multiplier": std_mult,
            "total_return": metrics["total_return"],
            "sharpe_ratio": metrics["sharpe_ratio"],
            "win_rate": metrics["win_rate"],
            "max_drawdown": metrics["max_drawdown"],
        })
    
    return pl.DataFrame(results)


# Run grid searches
print("Running z-score grid search...")
zscore_results = grid_search_zscores()
zscore_results.write_csv("/Users/xingjianliu/jim/quant/docs/zscore_grid_search.csv")

print("\nRunning window grid search...")
window_results = grid_search_windows()
window_results.write_csv("/Users/xingjianliu/jim/quant/docs/window_grid_search.csv")

print("\nRunning std multiplier grid search...")
std_results = grid_search_std()
std_results.write_csv("/Users/xingjianliu/jim/quant/docs/std_grid_search.csv")

print("\nAll grid searches complete!")
print("Results saved to docs/ directory")
