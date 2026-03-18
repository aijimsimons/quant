"""Test polymarket SDK."""

import polymarket

print("Polymarket SDK version:", polymarket.__version__)

# Check for testnet support
try:
    print("Has testnet:", hasattr(polymarket, 'Testnet'))
    print("Has Mainnet:", hasattr(polymarket, 'Mainnet'))
except Exception as e:
    print("Error:", e)
