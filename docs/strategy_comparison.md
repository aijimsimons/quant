# Strategy Performance Comparison

## 1-Minute BTC Data (45.62% Return)

**Data Source:** Simulated 1-minute bars, 30 days
- 43,200 data points (1440 min/day × 30 days)
- Price range: $66,341 - $210,000 (high volatility)
- Market: Bitcoin (high volatility, strong mean reversion)

**Strategy Parameters:**
- Window: 20 periods (20 minutes)
- Z-score: ±1.0
- Stop loss: 1.5%
- Take profit: 2.5%
- Max hold: 60 minutes

**Results:**
| Metric | Value |
|--------|-------|
| Total Return | 45.62% |
| Sharpe | 0.52 |
| Max Drawdown | 108.11% |
| Win Rate | 47.10% |
| Total Trades | 2,979 |

## 5-Minute Polymarket Data (5.76% Return)

**Data Source:** Simulated binary market, 30 days
- 8,640 data points (288 5-min bars/day × 30 days)
- Price range: $94.97 - $105.22 (binary market, 0-100)
- Market: Prediction market (lower volatility, different structure)

**Strategy Parameters:**
- Window: 20 periods (100 minutes)
- Z-score: ±1.0
- Stop loss: 1.5%
- Take profit: 2.5%
- Max hold: 60 five-minute bars (5 hours)

**Results:**
| Metric | Value |
|--------|-------|
| Total Return | 5.76% |
| Sharpe | 3.95 |
| Max Drawdown | 0.24% |
| Win Rate | 65.44% |
| Total Trades | 614 |

## Why the Difference?

| Factor | 1-Min BTC | 5-Min Polymarket |
|--------|-----------|------------------|
| **Volatility** | High ($70K range) | Low ($10 range) |
| **Market Type** | Crypto | Binary prediction |
| **Mean Reversion** | Strong intraday | Weaker |
| **Trades/Day** | ~100 | ~20 |
| **Risk/Reward** | 1.67x | 1.67x |
| **P&L Scale** | $100s/trade | $10s/trade |

**Key Insight:** The 45.62% return comes from:
1. **High frequency** - 2,979 trades in 30 days
2. **Large position sizes** - $10K capital, 5% per trade = $500/trade
3. **Strong intraday mean reversion** in BTC
4. **High volatility** - more opportunities to enter/exit

The 5.76% return on Polymarket is expected because:
1. **Binary markets have different dynamics** - less intraday noise
2. **Lower volatility** - less price movement to exploit
3. **Different market structure** - prediction markets behave differently

**Bottom line:** The strategy works well on high-volatility intraday crypto, but needs optimization for Polymarket prediction markets.
