# Quant - Trading Infrastructure & Strategies

A monorepo for quantitative crypto trading strategies and infrastructure.

## Structure

```
quant/
├── src/quant_core/      # Shared utilities
├── strategies/          # Trading strategies
├── infrastructure/      # Data pipelines, execution, risk
├── backtesting/         # Backtesting engine
├── observability/       # Monitoring, alerts
└── tests/               # Test suite
```

## Quick Start

```bash
cd quant
uv sync
```

## Projects

- **strategies/** - Mean reversion, momentum, stat arb, regime detection
- **infrastructure/** - Data pipelines, execution clients, risk management
- **backtesting/** - Comprehensive backtesting infrastructure
- **observability/** - Real-time monitoring and alerting
