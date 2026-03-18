from quant.infrastructure.data.real_data import load_bitcoin_ohlcv_csv
from quant.strategies.mean_reversion_bitcoin import mean_reversion_bitcoin, calculate_metrics
import polars as pl

btc_df = load_bitcoin_ohlcv_csv()

# Test a few parameter combinations
test_params = [
    (20, 1.5, -2.0, 2.0, 0.02, 0.03),
    (25, 2.0, -1.5, 1.5, 0.02, 0.03),
]

for window, std_mult, min_z, max_z, stop_loss, take_profit in test_params:
    print(f"\nTesting: window={window}, std={std_mult}, z=[{min_z},{max_z}]")
    
    # Run on full data
    data_polars = pl.from_pandas(btc_df)
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
    
    metrics = calculate_metrics(results, capital=10000.0)
    print(f"  Full data Sharpe: {metrics['sharpe_ratio']:.2f}, Win Rate: {metrics['win_rate']*100:.2f}%, Trades: {metrics['total_trades']}")
    
    # Walk-forward with 100-day windows
    window_size = 100
    n = len(btc_df)
    num_windows = n - window_size - 73 + 1
    
    window_sharpe_scores = []
    for i in range(0, num_windows, 5):  # Every 5th window
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
            
            train_end = int(window_size * 0.7)
            val_df = results.select(pl.all().slice(train_end, window_size - train_end))
            val_metrics = calculate_metrics(val_df, capital=10000.0)
            
            print(f"  Window {i}: Sharpe={val_metrics['sharpe_ratio']:.2f}, Trades={val_metrics['total_trades']}")
            
            if val_metrics['total_trades'] >= 3:
                window_sharpe_scores.append(val_metrics['sharpe_ratio'])
        except Exception as e:
            print(f"  Window {i}: Error - {e}")
    
    if window_sharpe_scores:
        avg_sharpe = sum(window_sharpe_scores) / len(window_sharpe_scores)
        print(f"  Avg Sharpe across {len(window_sharpe_scores)} windows: {avg_sharpe:.2f}")
