"""
ORB Strategy Backtesting Engine

This module provides backtesting functionality for the ORB strategy,
including trade execution simulation, performance metrics, and reporting.

Author: Algo Trading Project
Date: October 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, time
import logging

from .orb_strategy import ORBStrategy
from . import orb_config as config

logger = logging.getLogger(__name__)


class Trade:
    """Represents a single trade with entry/exit details."""

    def __init__(
        self,
        entry_time: datetime,
        entry_price: float,
        direction: str,
        shares: int,
        stops_targets: Dict[str, float],
        symbol: str = 'UNKNOWN'
    ):
        self.entry_time = entry_time
        self.entry_price = entry_price
        self.direction = direction
        self.shares = shares
        self.stops_targets = stops_targets
        self.symbol = symbol

        # Exit details (filled when trade closes)
        self.exit_time: Optional[datetime] = None
        self.exit_price: Optional[float] = None
        self.exit_reason: Optional[str] = None
        self.pnl: float = 0.0
        self.pnl_pct: float = 0.0
        self.r_multiple: float = 0.0
        self.holding_time: Optional[float] = None  # in hours

        # Track partial exits
        self.remaining_shares = shares
        self.partial_exits: List[Dict] = []

    def close_position(
        self,
        exit_time: datetime,
        exit_price: float,
        exit_reason: str,
        shares_to_close: Optional[int] = None
    ):
        """Close the position (or part of it)."""
        if shares_to_close is None:
            shares_to_close = self.remaining_shares

        # Calculate P&L for this exit
        if self.direction == 'long':
            trade_pnl = (exit_price - self.entry_price) * shares_to_close
        else:  # short
            trade_pnl = (self.entry_price - exit_price) * shares_to_close

        # Subtract commission
        commission = config.COMMISSION_PER_TRADE
        trade_pnl -= commission

        # Record partial exit if not closing entire position
        if shares_to_close < self.remaining_shares:
            self.partial_exits.append({
                'time': exit_time,
                'price': exit_price,
                'shares': shares_to_close,
                'pnl': trade_pnl,
                'reason': exit_reason
            })
            self.remaining_shares -= shares_to_close
            self.pnl += trade_pnl
        else:
            # Final exit
            self.exit_time = exit_time
            self.exit_price = exit_price
            self.exit_reason = exit_reason
            self.pnl += trade_pnl
            self.remaining_shares = 0

            # Calculate metrics
            self.pnl_pct = (self.pnl / (self.entry_price * self.shares)) * 100
            self.holding_time = (exit_time - self.entry_time).total_seconds() / 3600

            # Calculate R-multiple (risk-adjusted return)
            risk = abs(self.entry_price - self.stops_targets['initial_stop']) * self.shares
            self.r_multiple = self.pnl / risk if risk > 0 else 0

    def is_open(self) -> bool:
        """Check if position is still open."""
        return self.remaining_shares > 0

    def __repr__(self) -> str:
        status = "OPEN" if self.is_open() else "CLOSED"
        return (f"Trade({self.direction.upper()} {self.shares} @ {self.entry_price:.2f}, "
                f"Status={status}, PnL=${self.pnl:.2f})")


class ORBBacktest:
    """Backtesting engine for ORB strategy."""

    def __init__(
        self,
        strategy: ORBStrategy,
        initial_capital: float = config.INITIAL_CAPITAL
    ):
        """
        Initialize backtest engine.

        Parameters
        ----------
        strategy : ORBStrategy
            Strategy instance to backtest
        initial_capital : float
            Starting capital
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.current_capital = initial_capital

        # Trade tracking
        self.trades: List[Trade] = []
        self.open_positions: List[Trade] = []
        self.equity_curve: List[Dict] = []

        # Performance metrics
        self.metrics: Dict = {}

        logger.info(f"Backtest initialized with ${initial_capital:,.0f}")

    def run_backtest(self, df: pd.DataFrame, symbol: str = 'UNKNOWN') -> Tuple[pd.DataFrame, Dict]:
        """
        Execute full backtest on historical data.

        Parameters
        ----------
        df : pd.DataFrame
            Intraday OHLCV data with signals already generated
        symbol : str
            Symbol being traded

        Returns
        -------
        trades_df : pd.DataFrame
            DataFrame of all trades
        metrics : dict
            Performance metrics
        """
        logger.info(f"Starting backtest for {symbol}: {len(df)} bars from {df.index[0]} to {df.index[-1]}")

        # Process each bar
        for idx in df.index:
            bar = df.loc[idx]

            # Update equity curve
            self._update_equity(idx, bar)

            # Check for exits on open positions
            self._check_exits(idx, bar)

            # Check for new entry signals (only if no position open)
            if len(self.open_positions) == 0:
                if bar['long_signal']:
                    self._enter_trade(idx, bar, 'long', symbol, df)
                elif bar['short_signal']:
                    self._enter_trade(idx, bar, 'short', symbol, df)

        # Close any remaining open positions at end of backtest
        if len(self.open_positions) > 0:
            final_bar = df.iloc[-1]
            for position in self.open_positions:
                position.close_position(
                    exit_time=df.index[-1],
                    exit_price=final_bar['Close'],
                    exit_reason='End of data'
                )
            self.open_positions = []

        # Calculate performance metrics
        trades_df = self._create_trades_dataframe()
        self.metrics = self.calculate_performance(trades_df)

        logger.info(f"Backtest complete: {len(self.trades)} trades, Final capital: ${self.current_capital:,.0f}")

        return trades_df, self.metrics

    def _enter_trade(
        self,
        entry_time: datetime,
        bar: pd.Series,
        direction: str,
        symbol: str,
        df: pd.DataFrame
    ):
        """Enter a new trade."""
        # Get OR range for position sizing
        or_range = bar['OR_Range']
        atr = bar['ATR']

        # Calculate stops and targets
        stops_targets = self.strategy.calculate_stops_targets(
            entry_price=bar['Close'],
            or_range=or_range,
            direction=direction
        )

        # Calculate position size
        stop_distance = abs(bar['Close'] - stops_targets['initial_stop'])
        shares = self.strategy.calculate_position_size(
            capital=self.current_capital,
            stop_distance=stop_distance,
            price=bar['Close'],
            or_range=or_range,
            atr=atr
        )

        if shares <= 0:
            logger.warning(f"{entry_time}: Position size calculated as {shares}, skipping trade")
            return

        # Apply slippage to entry
        slippage = bar['Close'] * config.SLIPPAGE_PCT
        entry_price = bar['Close'] + slippage if direction == 'long' else bar['Close'] - slippage

        # Create trade object
        trade = Trade(
            entry_time=entry_time,
            entry_price=entry_price,
            direction=direction,
            shares=shares,
            stops_targets=stops_targets,
            symbol=symbol
        )

        # Add to open positions
        self.open_positions.append(trade)

        # Update capital (reserve for position)
        position_value = entry_price * shares
        commission = config.COMMISSION_PER_TRADE
        self.current_capital -= (position_value + commission)

        logger.info(f"{entry_time}: {direction.upper()} {shares} shares @ ${entry_price:.2f}, "
                   f"Stop: ${stops_targets['initial_stop']:.2f}")

    def _check_exits(self, current_time: datetime, bar: pd.Series):
        """Check exit conditions for all open positions."""
        positions_to_close = []

        for position in self.open_positions:
            exit_price = None
            exit_reason = None
            shares_to_exit = position.remaining_shares

            # Check time stop
            if current_time.time() >= time(config.TIME_STOP_HOUR, config.TIME_STOP_MINUTE):
                exit_price = bar['Close']
                exit_reason = 'Time stop'

            # Check stop loss
            elif position.direction == 'long':
                if bar['Low'] <= position.stops_targets['current_stop']:
                    exit_price = min(position.stops_targets['current_stop'], bar['Open'])
                    exit_reason = 'Stop loss'

            else:  # short
                if bar['High'] >= position.stops_targets['current_stop']:
                    exit_price = max(position.stops_targets['current_stop'], bar['Open'])
                    exit_reason = 'Stop loss'

            # Check profit targets (scaled exits)
            if exit_price is None:
                if position.direction == 'long':
                    # Target 3 (final 25%)
                    if bar['High'] >= position.stops_targets['target_3']:
                        if position.remaining_shares == int(position.shares * config.SCALE_OUT_PCT_3):
                            exit_price = position.stops_targets['target_3']
                            exit_reason = 'Target 3'
                            shares_to_exit = position.remaining_shares

                    # Target 2 (25%)
                    elif bar['High'] >= position.stops_targets['target_2']:
                        if position.remaining_shares > int(position.shares * config.SCALE_OUT_PCT_3):
                            exit_price = position.stops_targets['target_2']
                            exit_reason = 'Target 2'
                            shares_to_exit = int(position.shares * config.SCALE_OUT_PCT_2)

                    # Target 1 (50%)
                    elif bar['High'] >= position.stops_targets['target_1']:
                        if position.remaining_shares == position.shares:  # First exit
                            exit_price = position.stops_targets['target_1']
                            exit_reason = 'Target 1'
                            shares_to_exit = int(position.shares * config.SCALE_OUT_PCT_1)

                    # Move stop to breakeven after reaching breakeven trigger
                    if not position.stops_targets['stop_moved_to_be']:
                        if bar['High'] >= position.stops_targets['breakeven_trigger']:
                            position.stops_targets['current_stop'] = position.entry_price
                            position.stops_targets['stop_moved_to_be'] = True
                            logger.debug(f"{current_time}: Stop moved to breakeven @ ${position.entry_price:.2f}")

                else:  # short
                    # Similar logic for short positions
                    if bar['Low'] <= position.stops_targets['target_3']:
                        if position.remaining_shares == int(position.shares * config.SCALE_OUT_PCT_3):
                            exit_price = position.stops_targets['target_3']
                            exit_reason = 'Target 3'
                            shares_to_exit = position.remaining_shares

                    elif bar['Low'] <= position.stops_targets['target_2']:
                        if position.remaining_shares > int(position.shares * config.SCALE_OUT_PCT_3):
                            exit_price = position.stops_targets['target_2']
                            exit_reason = 'Target 2'
                            shares_to_exit = int(position.shares * config.SCALE_OUT_PCT_2)

                    elif bar['Low'] <= position.stops_targets['target_1']:
                        if position.remaining_shares == position.shares:
                            exit_price = position.stops_targets['target_1']
                            exit_reason = 'Target 1'
                            shares_to_exit = int(position.shares * config.SCALE_OUT_PCT_1)

                    if not position.stops_targets['stop_moved_to_be']:
                        if bar['Low'] <= position.stops_targets['breakeven_trigger']:
                            position.stops_targets['current_stop'] = position.entry_price
                            position.stops_targets['stop_moved_to_be'] = True

            # Execute exit if triggered
            if exit_price is not None:
                # Apply slippage
                slippage = exit_price * config.SLIPPAGE_PCT
                if position.direction == 'long':
                    exit_price -= slippage
                else:
                    exit_price += slippage

                # Close position (or part of it)
                position.close_position(
                    exit_time=current_time,
                    exit_price=exit_price,
                    exit_reason=exit_reason,
                    shares_to_close=shares_to_exit
                )

                # Update capital
                proceeds = exit_price * shares_to_exit
                self.current_capital += proceeds

                logger.info(f"{current_time}: EXIT {exit_reason} - {shares_to_exit} shares @ ${exit_price:.2f}, "
                           f"PnL: ${position.pnl:.2f}")

                # If fully closed, mark for removal
                if not position.is_open():
                    positions_to_close.append(position)
                    self.trades.append(position)

        # Remove closed positions
        for position in positions_to_close:
            self.open_positions.remove(position)

    def _update_equity(self, current_time: datetime, bar: pd.Series):
        """Update equity curve with current market values."""
        # Calculate open position values
        open_pnl = 0.0
        for position in self.open_positions:
            if position.direction == 'long':
                unrealized_pnl = (bar['Close'] - position.entry_price) * position.remaining_shares
            else:
                unrealized_pnl = (position.entry_price - bar['Close']) * position.remaining_shares
            open_pnl += unrealized_pnl

        total_equity = self.current_capital + open_pnl

        self.equity_curve.append({
            'timestamp': current_time,
            'equity': total_equity,
            'cash': self.current_capital,
            'open_pnl': open_pnl,
            'open_positions': len(self.open_positions)
        })

    def _create_trades_dataframe(self) -> pd.DataFrame:
        """Create DataFrame from completed trades."""
        if len(self.trades) == 0:
            return pd.DataFrame()

        trades_data = []
        for trade in self.trades:
            trades_data.append({
                'entry_time': trade.entry_time,
                'exit_time': trade.exit_time,
                'symbol': trade.symbol,
                'direction': trade.direction,
                'shares': trade.shares,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'pnl': trade.pnl,
                'pnl_pct': trade.pnl_pct,
                'r_multiple': trade.r_multiple,
                'holding_time_hours': trade.holding_time,
                'exit_reason': trade.exit_reason,
                'partial_exits': len(trade.partial_exits)
            })

        return pd.DataFrame(trades_data)

    def calculate_performance(self, trades_df: pd.DataFrame) -> Dict:
        """
        Calculate comprehensive performance metrics.

        Parameters
        ----------
        trades_df : pd.DataFrame
            DataFrame of completed trades

        Returns
        -------
        dict
            Performance metrics
        """
        if len(trades_df) == 0:
            logger.warning("No trades to analyze")
            return {}

        # Basic metrics
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] < 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # Return metrics
        total_pnl = trades_df['pnl'].sum()
        total_return = (self.current_capital - self.initial_capital) / self.initial_capital

        wins = trades_df[trades_df['pnl'] > 0]['pnl']
        losses = trades_df[trades_df['pnl'] < 0]['pnl']

        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0
        largest_win = wins.max() if len(wins) > 0 else 0
        largest_loss = abs(losses.min()) if len(losses) > 0 else 0

        # Profit factor
        total_wins = wins.sum() if len(wins) > 0 else 0
        total_losses = abs(losses.sum()) if len(losses) > 0 else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0

        # Risk-adjusted metrics
        avg_r_multiple = trades_df['r_multiple'].mean()

        # Calculate Sharpe ratio from equity curve
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df['returns'] = equity_df['equity'].pct_change()
        sharpe_ratio = (equity_df['returns'].mean() / equity_df['returns'].std() * np.sqrt(252)) \
            if equity_df['returns'].std() > 0 else 0

        # Max drawdown
        equity_df['cummax'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['cummax']) / equity_df['cummax']
        max_drawdown = abs(equity_df['drawdown'].min())

        # Strategy-specific metrics
        avg_or_range = trades_df.get('or_range', pd.Series([0])).mean()
        avg_holding_time = trades_df['holding_time_hours'].mean()

        # Compile metrics
        metrics = {
            # Win Rate Metrics
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,

            # Return Metrics
            'total_pnl': total_pnl,
            'total_return_pct': total_return * 100,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'profit_factor': profit_factor,

            # Risk Metrics
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_pct': max_drawdown * 100,
            'avg_r_multiple': avg_r_multiple,

            # Strategy Specific
            'avg_or_range': avg_or_range,
            'avg_holding_time_hours': avg_holding_time,

            # Capital
            'initial_capital': self.initial_capital,
            'final_capital': self.current_capital,
        }

        return metrics

    def generate_report(self, save_path: Optional[str] = None) -> str:
        """
        Generate detailed performance report.

        Parameters
        ----------
        save_path : str, optional
            Path to save report markdown file

        Returns
        -------
        str
            Report as markdown text
        """
        if not self.metrics:
            return "No backtest results available"

        m = self.metrics

        report = f"""# ORB Strategy Backtest Results

## Summary Statistics

- **Total Trades**: {m['total_trades']}
- **Win Rate**: {m['win_rate']*100:.1f}%
- **Total Return**: {m['total_return_pct']:.2f}%
- **Sharpe Ratio**: {m['sharpe_ratio']:.2f}
- **Max Drawdown**: {m['max_drawdown_pct']:.2f}%
- **Profit Factor**: {m['profit_factor']:.2f}

## Trade Analysis

- **Winning Trades**: {m['winning_trades']}
- **Losing Trades**: {m['losing_trades']}
- **Average Win**: ${m['avg_win']:.2f}
- **Average Loss**: ${m['avg_loss']:.2f}
- **Largest Win**: ${m['largest_win']:.2f}
- **Largest Loss**: ${m['largest_loss']:.2f}

## Risk-Adjusted Returns

- **Average R-Multiple**: {m['avg_r_multiple']:.2f}
- **Sharpe Ratio**: {m['sharpe_ratio']:.2f}

## Strategy Metrics

- **Average Holding Time**: {m['avg_holding_time_hours']:.2f} hours
- **Average OR Range**: ${m['avg_or_range']:.2f}

## Capital

- **Initial Capital**: ${m['initial_capital']:,.0f}
- **Final Capital**: ${m['final_capital']:,.0f}
- **Total P&L**: ${m['total_pnl']:,.2f}

---

*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        if save_path:
            with open(save_path, 'w') as f:
                f.write(report)
            logger.info(f"Report saved to {save_path}")

        return report


if __name__ == '__main__':
    print("ORB Backtest Engine - Run this via main backtest script")
