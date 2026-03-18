"""Metrics calculation for quant strategies."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime


class StrategyMetrics:
    """Calculate comprehensive strategy performance metrics."""
    
    def __init__(self, capital: float = 10000.0):
        self.capital = capital
    
    def calculate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all strategy metrics."""
        metrics = {}
        
        # Basic returns
        equity = df['equity']
        metrics['total_return'] = (equity.iloc[-1] - self.capital) / self.capital if len(equity) > 1 else 0
        
        # Daily returns
        returns = df['returns'].dropna()
        if len(returns) > 0:
            metrics['sharpe_ratio'] = (returns.mean() / returns.std()) * (252 * 24) ** 0.5 if returns.std() > 0 else 0
        else:
            metrics['sharpe_ratio'] = 0
        
        # Drawdown
        rolling_max = equity.cummax()
        drawdown = (rolling_max - equity) / rolling_max
        metrics['max_drawdown'] = drawdown.max() if len(drawdown) > 1 else 0
        
        # P&L analysis
        pnl = df['pnl'].dropna()
        wins = pnl[pnl > 0]
        losses = pnl[pnl < 0]
        
        metrics['win_rate'] = len(wins) / len(pnl) if len(pnl) > 0 else 0
        metrics['profit_factor'] = abs(wins.sum() / losses.sum()) if len(losses) > 0 and losses.sum() != 0 else float('inf')
        metrics['avg_win'] = float(wins.mean()) if len(wins) > 0 else 0.0
        metrics['avg_loss'] = float(losses.mean()) if len(losses) > 0 else 0.0
        
        # Trade analysis
        position_changes = df['position'].diff().abs().sum()
        metrics['total_trades'] = int(position_changes // 2) if position_changes > 0 else 0
        
        # Risk-adjusted returns
        if len(returns) > 0:
            metrics['sortino_ratio'] = (returns.mean() / returns[returns < 0].std()) * (252 * 24) ** 0.5 if returns[returns < 0].std() > 0 else 0
        else:
            metrics['sortino_ratio'] = 0
        
        # Calmar ratio (return / max drawdown)
        metrics['calmar_ratio'] = metrics['total_return'] / abs(metrics['max_drawdown']) if metrics['max_drawdown'] > 0 else 0
        
        # Equity stats
        metrics['final_equity'] = float(equity.iloc[-1]) if len(equity) > 1 else float(self.capital)
        metrics['peak_equity'] = float(equity.max()) if len(equity) > 1 else float(self.capital)
        metrics['min_equity'] = float(equity.min()) if len(equity) > 1 else float(self.capital)
        
        return metrics


class PortfolioMetrics:
    """Portfolio-level metrics across multiple strategies."""
    
    def __init__(self, capital: float = 10000.0):
        self.capital = capital
        self.strategy_metrics = StrategyMetrics(capital)
    
    def calculate(self, strategy_results: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate portfolio metrics from multiple strategy results."""
        portfolio_metrics = {
            'total_return': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'total_trades': 0,
            'strategies': {}
        }
        
        total_equity = pd.Series([self.capital])
        
        for name, df in strategy_results.items():
            metrics = self.strategy_metrics.calculate(df)
            portfolio_metrics['strategies'][name] = metrics
            portfolio_metrics['total_trades'] += metrics['total_trades']
            
            # Accumulate equity curves
            if 'equity' in df.columns:
                total_equity = total_equity.add(df['equity'].dropna(), fill_value=0)
        
        # Calculate portfolio-level metrics
        if len(total_equity) > 1:
            portfolio_metrics['total_return'] = (total_equity.iloc[-1] - self.capital) / self.capital
            portfolio_metrics['peak_equity'] = float(total_equity.max())
            portfolio_metrics['min_equity'] = float(total_equity.min())
            
            returns = total_equity.pct_change().dropna()
            if len(returns) > 0 and returns.std() > 0:
                portfolio_metrics['sharpe_ratio'] = (returns.mean() / returns.std()) * (252 * 24) ** 0.5
        
        return portfolio_metrics
