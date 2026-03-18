from quant.infrastructure.data.real_data import load_bitcoin_ohlcv_csv
from quant.strategies.mean_reversion_bitcoin import mean_reversion_bitcoin, calculate_metrics
import polars as pl

btc_df = load_bitcoin_ohlcv_csv()
n = len(btc_df)
window_size = 100
test_size = 73
train_ratio = 0.7
num_windows = n - window_size - test_size + 1

# Test a few aggressive parameter combinations
test_params = [
    (3, 0.8, -0.5, 0.5, 0.005, 0.01),
    (5, 1.0, -0.6, 0.6, 0.01, 0.02),
    (7, 1.2, -0.8, 0.8, 0.01, 0.02),
]

for window, std_mult, min_z, max_z, stop_loss, take_profit in test_params:
    print(f"\nTesting: w={window}, std={std_mult}, z=[{min_z},{max_z}], sl={stop_loss}, tp={take_profit}")
    
    window_sharpe_scores = []
    trade_counts = []
    
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
            
            trade_counts.append(val_metrics['total_trades'])
            if val_metrics['total_trades'] >= 5:
                window_sharpe_scores.append(val_metrics['sharpe_ratio'])
        except Exception as e:
            print(f"  Window {i}: Error - {e}")
    
    print(f"  Windows with >=5 trades: {len(window_sharpe_scores)}/{len(trade_counts)}")
    print(f"  Trade counts: {set(trade_counts)}")
    if window_sharpe_scores:
        avg_sharpe = sum(window_sharpe_scores) / len(window_sharpe_scores)
        print(f"  Avg Sharpe (with >=5 trades): {avg_sharpe:.2f}")
