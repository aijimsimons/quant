# Polymarket Testnet

## What is Testnet?

**Testnet** is Polymarket's **testing environment** where you can:

- ✅ **Trade with fake money** - No real funds at risk
- ✅ **Test API integration** - Verify your code works
- ✅ **Practice strategies** - Test before going live
- ✅ **Develop and iterate** - Fast experimentation

## How It Works

```
Mainnet (Real Money)          Testnet (Fake Money)
    ↓                              ↓
$1,000,000,000+ TVL            ~$0 TVL
Real BTC/ETH trades            Simulated trades
Real USD deposits              Fake USD deposits
Actual market impact           Simulated market impact
```

## Access Testnet

1. **Visit**: https://testnet.polymarket.com
2. **Connect Wallet** (use testnet wallet)
3. **Get Testnet Funds** - Usually auto-funded
4. **Get API Keys** - From dashboard → API Keys

## API Keys

### Testnet API Keys
```
# In ~/.env
POLYMARKET_API_KEY=your_testnet_api_key
POLYMARKET_SECRET=your_testnet_secret
POLYMARKET_TESTNET=true
```

### Mainnet API Keys
```
# In ~/.env
POLYMARKET_API_KEY=your_mainnet_api_key
POLYMARKET_SECRET=your_mainnet_secret
POLYMARKET_TESTNET=false
```

## Testnet vs Mainnet

| Feature | Testnet | Mainnet |
|---------|---------|---------|
| **Money** | Fake USD | Real USD |
| **TVL** | Minimal | $1B+ |
| **Markets** | Simulated | Real prediction markets |
| **Liquidity** | Low | High |
| **Fees** | Real fees | Real fees |
| **API Access** | Same | Same |

## Using Testnet for Paper Trading

```python
from quant.infrastructure.polymarket import PolymarketClient

# Testnet (paper trading)
client = PolymarketClient(
    api_key="your_testnet_key",
    testnet=True,  # ← This is key!
)

# Get markets
markets = client.get_markets()
print(f"Testnet markets: {len(markets)}")

# Get prices
prices = client.get_prices("market_id", period="24h", interval="5m")
print(f"Testnet prices: {len(prices)} bars")
```

## Getting Testnet Access

1. Go to https://testnet.polymarket.com
2. Connect your wallet
3. You'll typically get testnet funds automatically
4. For API access, check the documentation

## Important Notes

- Testnet uses the **same API endpoints** as mainnet
- Testnet uses **testnet API keys** (different from mainnet keys)
- Testnet data is **not real market data** (simulated)
- Testnet is for **development and testing only**

## Production Checklist

Before going live on mainnet:
- [ ] Paper trade on testnet for 2+ weeks
- [ ] Verify API integration
- [ ] Test risk management
- [ ] Test kill switches
- [ ] Document runbook
- [ ] Set up monitoring
- [ ] Get mainnet API keys

## Next Steps

1. Create testnet account
2. Get testnet API keys
3. Connect to real Polymarket data
4. Run mean reversion strategy on testnet
5. Verify P&L calculations
6. Deploy to production with mainnet keys
