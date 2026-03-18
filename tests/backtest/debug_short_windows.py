from quant.infrastructure.data.real_data import load_bitcoin_ohlcv_csv
from quant.strategies.mean_reversion_bitcoin import mean_reversion_bitcoin, calculate_metrics
import polars as pl

btc_df = load_bitcoin_ohlcv_csv()
n = len(btc_df)

# Test with shorter windows (50 days instead of 100)
window_size = 50
test_size = 73
train_ratio = 0.7
num_windows = n - window_size - test_size + 1

print(f"Testing with {window_size}-day windows, {num_windows} total windows")

# Test with very tight z-scores
window = 3
std_mult = 0.6
min_z, max_z = -0.4, 0.4
stop_loss = 0.005
take_profit = 0.01

print(f"Params: w={window}, std={std_mult}, z=[{min_z},{max_z}], sl={stop_loss}, tp={take_profit}")

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
        print(f"  Window {i}: Trades={val_metrics['total_trades']}, Sharpe={val_metrics['sharpe_ratio']:.2f}")
        
        if val_metrics['total_trades'] >= 3:
            window_sharpe_scores.append(val_metrics['sharpe_ratio'])
    except Exception as e:
        print(f"  Window {i}: Error - {e}")

print(f"\nWindows with >=3 trades: {len(window_sharpe_scores)}/{len(trade_counts)}")
print(f"Trade counts: {set(trade_counts)}")
if window_sharpe_scores:
    avg_sharpe = sum(window_sharpe_scores) / len(window_sharpe_scores)
    print(f"Avg Sharpe (with >=3 trades): {avg_sharpe:.2f}")
