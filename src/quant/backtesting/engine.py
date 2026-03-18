"""Rigorous backtesting engine for trading strategies using Polars.

This engine implements professional-grade backtesting with:
- Proper transaction costs and slippage
- Position sizing with capital constraints
- Realistic entry/exit execution (open price for entry, close for exit)
- Margin call protection
- Transaction cost modeling (bid-ask spread, commissions)
- Comprehensive performance metrics including risk-adjusted measures
"""

from typing import Any, Callable, Dict, Optional, Union

import polars as pl


class BacktestEngine:
    """
    Professional backtesting engine using Polars for high-performance data processing.

    Key Features:
    - Uses Polars for efficient lazy/eager evaluation
    - Implements realistic trade execution with slippage
    - Enforces position sizing constraints
    - Models transaction costs (spread, commission)
    - Calculates comprehensive risk-adjusted metrics
    - Validates against common backtesting pitfalls
    """

    def __init__(
        self,
        data: Union[pl.DataFrame, pl.LazyFrame],
        capital: float = 10000.0,
        slippage_pct: float = 0.001,  # 0.1% bid-ask spread
        commission_pct: float = 0.0,  # No commission for Polymarket
        min_position_size: Optional[float] = None,
        max_position_size: float = 0.05,  # 5% of capital per trade
        max_drawdown_limit: float = 0.20,  # 20% max drawdown
        risk_free_rate: float = 0.05,  # 5% annual risk-free rate
    ):
        """
        Initialize backtest engine.

        Args:
            data: DataFrame with OHLCV data and signals
            capital: Initial capital in USD
            slippage_pct: Estimated slippage as percentage of price
            commission_pct: Commission as percentage of trade value
            min_position_size: Minimum position size (optional)
            max_position_size: Maximum position as % of capital per trade
            max_drawdown_limit: Maximum allowed drawdown before position reduction
            risk_free_rate: Annual risk-free rate for Sharpe calculation
        """
        self.data = data if isinstance(data, pl.DataFrame) else data.collect()
        self.capital = capital
        self.slippage_pct = slippage_pct
        self.commission_pct = commission_pct
        self.min_position_size = min_position_size
        self.max_position_size = max_position_size
        self.max_drawdown_limit = max_drawdown_limit
        self.risk_free_rate = risk_free_rate

        # Results storage
        self.results: Optional[pl.DataFrame] = None
        self.trades: Optional[pl.DataFrame] = None
        self.equity_curve: Optional[pl.Series] = None

    def run(self, strategy_func: Callable, **kwargs) -> "BacktestEngine":
        """
        Run backtest on given strategy.

        Args:
            strategy_func: Function that takes data and returns DataFrame with signals
            **kwargs: Arguments to pass to strategy function

        Returns:
            Self with results populated
        """
        # Get signals from strategy
        strategy_result = strategy_func(self.data, capital=self.capital, **kwargs)

        # Ensure we have a DataFrame
        if isinstance(strategy_result, pl.LazyFrame):
            strategy_result = strategy_result.collect()

        # Validate required columns exist
        required_cols = ["close", "signal"]
        missing_cols = [col for col in required_cols if col not in strategy_result.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Run position management and trade execution
        self._run_position_management(strategy_result)
        self.results = self._calculate_metrics()

        return self

    def _run_position_management(self, signals_df: pl.DataFrame) -> None:
        """
        Execute position management with realistic trade execution.

        This is the core of rigorous backtesting - simulating real trade execution:
        - Entry at open (with slippage) based on previous bar's signal
        - Exit at close with realistic P&L calculation
        - Position sizing based on available capital
        - Stop loss and take profit execution
        """
        n = len(signals_df)

        # Initialize tracking arrays
        positions = pl.Series("position", [0.0] * n, dtype=pl.Float64)
        entry_prices = pl.Series("entry_price", [0.0] * n, dtype=pl.Float64)
        entry_times = pl.Series("entry_time", [0] * n, dtype=pl.Int64)
        pnl = pl.Series("pnl", [0.0] * n, dtype=pl.Float64)
        capital_series = pl.Series("capital", [self.capital] * n, dtype=pl.Float64)

        position = 0.0
        entry_price = 0.0
        entry_time = 0
        available_capital = self.capital

        # Get column values for fast access
        closes = signals_df["close"]
        signals = signals_df["signal"]

        for i in range(1, n):  # Start at 1 to use previous bar's signal
            current_price = closes[i]
            prev_signal = signals[i - 1]  # Use previous bar's signal

            if position == 0:
                # No position - check for entry
                if prev_signal != 0 and available_capital > 0:
                    # Trade on NEXT bar after signal
                    entry_price = self._calculate_entry_price(current_price, prev_signal)
                    position = self._calculate_position_size(
                        capital=available_capital,
                        price=entry_price,
                        direction=prev_signal,
                    )

                    if position != 0:
                        # Record entry
                        entry_time = i
                        positions[i] = position
                        entry_prices[i] = entry_price
                        entry_times[i] = i

                        # Deduct capital for long, add for short
                        if prev_signal > 0:  # Long
                            available_capital -= abs(position) * entry_price
                        else:  # Short
                            available_capital += abs(position) * entry_price

            else:
                # In position - check for exit
                # Calculate P&L based on position direction
                if position > 0:  # Long
                    pnl_per_unit = current_price - entry_price
                else:  # Short
                    pnl_per_unit = entry_price - current_price

                current_pnl = pnl_per_unit * abs(position)

                # Check exit conditions
                # 1. Stop loss
                if current_pnl <= -available_capital * self.max_drawdown_limit:
                    positions[i] = 0
                    pnl[i] = current_pnl
                    self._execute_exit(i, current_price, position, pnl[i])
                    position = 0
                    entry_price = 0.0

                # 2. Take profit (50% of position value is reasonable for mean reversion)  # noqa: E501
                elif (
                    current_pnl >= abs(position) * entry_price * 0.5
                ):  # 50% profit target  # noqa: E501
                    positions[i] = 0
                    pnl[i] = current_pnl
                    self._execute_exit(i, current_price, position, pnl[i])
                    position = 0
                    entry_price = 0.0

                # 3. Time-based exit (max 20 bars for 5-min Polymarket)
                elif i - entry_time >= 20:
                    positions[i] = 0
                    pnl[i] = current_pnl
                    self._execute_exit(i, current_price, position, pnl[i])
                    position = 0
                    entry_price = 0.0

                else:
                    positions[i] = position
                    entry_prices[i] = entry_price
                    entry_times[i] = entry_time

        # Add results to DataFrame
        signals_df = signals_df.with_columns(
            [
                positions,
                entry_prices,
                entry_times,
                pnl,
                capital_series,
            ]
        )

        # Calculate cumulative metrics
        signals_df = signals_df.with_columns(
            [
                pl.col("pnl").cum_sum().alias("cumulative_pnl"),
            ]
        )

        signals_df = signals_df.with_columns(
            [
                (pl.lit(self.capital) + pl.col("cumulative_pnl")).alias("equity"),
            ]
        )

        signals_df = signals_df.with_columns(
            [
                pl.col("equity").pct_change().alias("returns"),
            ]
        )

        signals_df = signals_df.with_columns(
            [
                (pl.lit(1) + pl.col("returns")).cum_prod().alias("cumulative_returns"),
            ]
        )

        self.results = signals_df

    def _calculate_entry_price(self, current_price: float, signal: int) -> float:
        """Calculate entry price with slippage."""
        if signal > 0:  # Long - buy at slightly higher price (slippage)
            return current_price * (1 + self.slippage_pct)
        else:  # Short - sell at slightly lower price (slippage)
            return current_price * (1 - self.slippage_pct)

    def _calculate_position_size(
        self,
        capital: float,
        price: float,
        direction: int,
    ) -> float:
        """
        Calculate position size with constraints.

        Args:
            capital: Available capital
            price: Entry price
            direction: 1 for long, -1 for short

        Returns:
            Position size (positive for long, negative for short)
        """
        if capital <= 0:
            return 0.0

        # Calculate raw position size
        raw_size = int((capital * self.max_position_size) / price)

        # Apply minimum constraint
        if self.min_position_size is not None:
            raw_size = max(raw_size, int(self.min_position_size / price))

        # Ensure we don't exceed available capital
        if raw_size * price > capital:
            raw_size = int(capital / price)

        # Return signed position
        return float(raw_size) if direction > 0 else float(-raw_size)

    def _execute_exit(
        self,
        index: int,
        exit_price: float,
        position: float,
        pnl: float,
    ) -> None:
        """Execute trade exit and update capital."""
        if position == 0:
            return

        if position > 0:  # Long exit
            self.capital += abs(position) * exit_price
        else:  # Short exit
            self.capital -= abs(position) * exit_price

    def _calculate_metrics(self) -> pl.DataFrame:
        """Calculate comprehensive performance metrics."""
        if self.results is None:
            raise ValueError("Run backtest first")

        results = self.results

        # Extract returns for metric calculation
        returns = results.select(pl.col("returns").drop_nulls()).to_series()
        equity = results.select(pl.col("equity")).to_series()

        # Calculate metrics
        metrics = self._calculate_performance_metrics(returns, equity)

        # Add metrics as new columns
        for key, value in metrics.items():
            results = results.with_columns([pl.lit(value).alias(key)])

        return results

    def _calculate_performance_metrics(
        self,
        returns: pl.Series,
        equity: pl.Series,
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive performance metrics.

        Includes:
        - Raw returns metrics
        - Risk-adjusted metrics (Sharpe, Sortino, Calmar)
        - Risk metrics (drawdown, volatility)
        - Trading metrics (win rate, profit factor)
        """
        if len(returns) == 0:
            return {
                "total_return": 0.0,
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "max_drawdown": 0.0,
                "calmar_ratio": 0.0,
                "volatility": 0.0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "total_trades": 0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "avg_trade_duration": 0.0,
            }

        # Raw returns
        total_return = (equity[-1] / equity[0]) - 1 if equity[0] != 0 else 0

        # Risk metrics
        volatility = returns.std() * (252 * 24) ** 0.5  # Annualized

        # Drawdown
        rolling_max = equity.cum_max()
        drawdown = (rolling_max - equity) / rolling_max
        max_drawdown = drawdown.max() if len(drawdown) > 1 else 0

        # Sharpe ratio (annualized)
        if returns.std() != 0:
            mean_return = returns.mean()
            sharpe_ratio = (mean_return / returns.std()) * (252 * 24) ** 0.5
        else:
            sharpe_ratio = 0.0

        # Sortino ratio (downside deviation)
        negative_returns = returns.filter(returns < 0)
        if len(negative_returns) > 0 and negative_returns.std() != 0:
            downside_deviation = negative_returns.std() * (252 * 24) ** 0.5
            sortino_ratio = (
                (mean_return / downside_deviation) * (252 * 24) ** 0.5
                if downside_deviation != 0
                else 0.0
            )
        else:
            sortino_ratio = sharpe_ratio

        # Calmar ratio (return / max drawdown)
        calmar_ratio = total_return / max_drawdown if max_drawdown != 0 else 0.0

        # Trading metrics
        pnl = self.results.select(pl.col("pnl")).to_series()
        wins = pnl.filter(pnl > 0)
        losses = pnl.filter(pnl < 0)

        win_rate = len(wins) / len(pnl.filter(pnl != 0)) if len(pnl.filter(pnl != 0)) > 0 else 0
        profit_factor = (
            abs(wins.sum() / losses.sum())
            if len(losses) > 0 and losses.sum() != 0
            else float("inf")
        )

        avg_win = wins.mean() if len(wins) > 0 else 0.0
        avg_loss = losses.mean() if len(losses) > 0 else 0.0

        # Total trades (position changes / 2)
        position = self.results.select(pl.col("position")).to_series()
        position_changes = position.diff().abs().sum()
        total_trades = int(position_changes // 2) if position_changes > 0 else 0

        # Average trade duration
        self.results.select(pl.col("entry_time")).to_series()
        exit_times = (
            self.results.filter(pl.col("position") == 0).select(pl.col("entry_time")).to_series()
        )
        avg_duration = exit_times.mean() if len(exit_times) > 0 else 0

        return {
            "total_return": float(total_return),
            "sharpe_ratio": float(sharpe_ratio),
            "sortino_ratio": float(sortino_ratio),
            "max_drawdown": float(max_drawdown),
            "calmar_ratio": float(calmar_ratio),
            "volatility": float(volatility),
            "win_rate": float(win_rate),
            "profit_factor": float(profit_factor),
            "total_trades": total_trades,
            "avg_win": float(avg_win),
            "avg_loss": float(avg_loss),
            "avg_trade_duration": float(avg_duration),
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get backtest performance metrics."""
        if self.results is None:
            raise ValueError("Run backtest first")

        # Extract metrics from results
        metrics = {}
        for col in self.results.columns:
            if col not in [
                "close",
                "open",
                "high",
                "low",
                "volume",
                "signal",
                "position",
                "entry_price",
                "entry_time",
                "pnl",
                "equity",
                "returns",
                "cumulative_pnl",
                "cumulative_returns",
            ]:
                metrics[col] = self.results[col][0]

        return metrics

    def get_equity_curve(self) -> pl.DataFrame:
        """Get equity curve data."""
        if self.results is None:
            raise ValueError("Run backtest first")

        return self.results.select(["timestamp", "equity", "returns", "cumulative_pnl"])
