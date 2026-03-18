"""Backtesting engine for trading strategies."""

import pandas as pd
from typing import Callable, Dict, Any


class BacktestEngine:
    """Simple backtesting engine for strategy evaluation."""
    
    def __init__(self, data: pd.DataFrame, capital: float = 10000.0):
        """
        Initialize backtest engine.
        
        Args:
            data: DataFrame with price data
            capital: Initial capital in USD
        """
        self.data = data.copy()
        self.capital = capital
        self.results = None
        
    def run(self, strategy_func: Callable, **kwargs) -> pd.DataFrame:
        """
        Run backtest on given strategy.
        
        Args:
            strategy_func: Strategy function that returns DataFrame with signals
            **kwargs: Arguments to pass to strategy function
            
        Returns:
            DataFrame with strategy results
        """
        self.results = strategy_func(self.data, capital=self.capital, **kwargs)
        return self.results
    
    def get_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics from backtest results."""
        if self.results is None:
            raise ValueError("Run backtest first")
        
        returns = self.results['returns'].dropna()
        
        if len(returns) == 0 or returns.std() == 0:
            sharpe = 0.0
        else:
            sharpe = (returns.mean() / returns.std()) * (252 * 24) ** 0.5
        
        equity = self.results['equity']
        rolling_max = equity.cummax()
        drawdown = (rolling_max - equity) / rolling_max
        max_dd = drawdown.max() if len(drawdown) > 1 else 0
        
        wins = self.results[self.results['pnl'] > 0]['pnl']
        losses = self.results[self.results['pnl'] < 0]['pnl']
        win_rate = len(wins) / len(self.results[self.results['pnl'] != 0]) if len(self.results[self.results['pnl'] != 0]) > 0 else 0
        profit_factor = abs(wins.sum() / losses.sum()) if len(losses) > 0 and losses.sum() != 0 else float('inf')
        
        position_changes = self.results['position'].diff().abs().sum()
        total_trades = int(position_changes // 2) if position_changes > 0 else 0
        
        avg_win = wins.mean() if len(wins) > 0 else 0.0
        avg_loss = losses.mean() if len(losses) > 0 else 0.0
        
        return {
            'total_return': (equity.iloc[-1] - self.capital) / self.capital if len(equity) > 1 else 0,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_trades': total_trades,
            'avg_win': float(avg_win),
            'avg_loss': float(avg_loss),
        }
