"""Run all backtests and generate a comprehensive report."""

from quant.strategies.mean_reversion_polymarket import mean_reversion_polymarket, calculate_metrics
from quant.infrastructure.simulation import generate_polymarket_price_data
import polars as pl


def run_backtest_scenario(
    scenario_name: str,
    n_days: int = 30,
    start_price: float = 50.0,
    volatility: float = 0.8,
    window: int = 20,
    std_multiplier: float = 1.5,
    min_zscore: float = -0.8,
    max_zscore: float = 0.8,
    **kwargs
) -> dict:
    """Run a single backtest scenario."""
    # Generate data
    data_pd = generate_polymarket_price_data(
        market_id=f"{scenario_name}-binary",
        n_days=n_days,
        start_price=start_price,
        volatility=volatility,
        drift=0.0,
        interval_minutes=5,
    )
    
    data = pl.from_pandas(data_pd)
    
    # Run strategy
    results = mean_reversion_polymarket(
        data,
        capital=10000.0,
        window=window,
        std_multiplier=std_multiplier,
        min_zscore=min_zscore,
        max_zscore=max_zscore,
        verbose=False,
        **kwargs
    )
    
    # Calculate metrics
    metrics = calculate_metrics(results, capital=10000.0)
    
    return {
        "scenario": scenario_name,
        "n_days": n_days,
        "volatility": volatility,
        "window": window,
        "std_multiplier": std_multiplier,
        **metrics
    }


# Run multiple scenarios
scenarios = [
    {"name": "baseline", "volatility": 0.8},
    {"name": "low_vol", "volatility": 0.4},
    {"name": "high_vol", "volatility": 1.2},
    {"name": "tight_zscore", "volatility": 0.8, "min_zscore": -0.6, "max_zscore": 0.6},
    {"name": "loose_zscore", "volatility": 0.8, "min_zscore": -1.0, "max_zscore": 1.0},
]

results = []
for scenario in scenarios:
    name = scenario.pop("name")
    print(f"Running scenario: {name}")
    result = run_backtest_scenario(name, **scenario)
    results.append(result)

# Print summary
print("\n" + "=" * 80)
print("BACKTEST SCENARIO RESULTS")
print("=" * 80)

for r in results:
    print(f"\n{r['scenario']}:")
    print(f"  Total Return:     {r['total_return']*100:+.2f}%")
    print(f"  Sharpe Ratio:     {r['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown:     {r['max_drawdown']*100:+.2f}%")
    print(f"  Win Rate:         {r['win_rate']*100:.2f}%")
    print(f"  Profit Factor:    {r['profit_factor']:.2f}")
    print(f"  Total Trades:     {r['total_trades']}")

# Save to file
results_df = pl.DataFrame(results)
results_df.write_csv("/Users/xingjianliu/jim/quant/docs/backtest_results.csv")

print("\nResults saved to docs/backtest_results.csv")
