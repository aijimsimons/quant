# Polymarket Paper Trading

## Setup

1. **Get API Keys**
   - Testnet: https://testnet.polymarket.com
   - Mainnet: https://polymarket.com/dashboard/api-keys

2. **Configure Environment**
```bash
# Add to .env
POLYMARKET_API_KEY=your_api_key
POLYMARKET_SECRET=your_secret
POLYMARKET_TESTNET=true
```

## Usage

### Real Trading
```python
from quant.infrastructure.polymarket import PolymarketClient

client = PolymarketClient(
    api_key="your_key",
    secret="your_secret",
    testnet=False,  # Mainnet
)

# Get markets
markets = client.get_markets(limit=10)

# Get orderbook
orderbook = client.get_orderbook("market_id")

# Place order
order = client.place_order(
    market_id="market_id",
    side="buy",
    price=100.0,
    size=10.0,
)
```

### Paper Trading
```python
from quant.infrastructure.polymarket import PaperPolymarketClient

client = PaperPolymarketClient(
    initial_balance=10000.0,
    testnet=True,
)

# Simulate order placement
order = client.place_order(
    market_id="market_id",
    side="buy",
    price=100.0,
    size=10.0,
)

# Simulate fill
client.fill_order(order, fill_price=102.0)

# Check position
position = client.get_position("market_id")

# Calculate P&L
pnl = client.get_final_pnl()
```

## Paper Trading Pipeline

```python
from quant.infrastructure.polymarket import PaperPolymarketClient
from strategies.mean_reversion import mean_reversion_strategy

# Initialize paper client
client = PaperPolymarketClient(initial_balance=10000.0)

# Get real Polymarket data
price_data = client.get_prices("market_id", period="24h", interval="5m")

# Run strategy
results = mean_reversion_strategy(price_data)

# Calculate paper P&L
metrics = calculate_metrics(results)
print(f"Paper P&L: ${metrics['total_return']*10000:,.2f}")
```

## Key Features

- **Zero real money** - Full simulation
- **Real API data** - Use actual Polymarket prices
- **Full order flow** - Track orders, fills, positions
- **P&L tracking** - Real-time and final P&L
- **Position management** - Track open positions

## Next Steps

1. Test with Polymarket testnet
2. Run mean reversion strategy
3. Verify P&L calculations
4. Deploy to production with real client
