"""
Opening Range Breakout (ORB) Strategy Implementation

This module implements the core ORB strategy logic including:
- Opening range identification
- Signal generation
- Entry/exit rules
- Position sizing
- Risk management

Author: Algo Trading Project
Date: October 2025
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Optional, List
from datetime import time, datetime, timedelta
import logging

# Import configuration
from . import orb_config as config

# Setup logging
logging.basicConfig(
    level=logging.INFO if config.VERBOSE_LOGGING else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ORBStrategy:
    """
    Opening Range Breakout Strategy Implementation

    This class encapsulates all logic for identifying opening ranges,
    generating signals, and managing trades according to the ORB methodology.
    """

    def __init__(
        self,
        or_period: int = config.OR_PERIOD_MINUTES,
        risk_reward: float = config.PROFIT_TARGET_3_MULTIPLIER,
        initial_capital: float = config.INITIAL_CAPITAL
    ):
        """
        Initialize ORB Strategy.

        Parameters
        ----------
        or_period : int
            Opening range period in minutes (15 or 30)
        risk_reward : float
            Risk/reward ratio for final profit target
        initial_capital : float
            Starting capital for position sizing
        """
        self.or_period = or_period
        self.risk_reward = risk_reward
        self.initial_capital = initial_capital
        self.current_capital = initial_capital

        # Track strategy state
        self.daily_pnl = 0.0
        self.trade_count_today = {}
        self.current_positions = []

        logger.info(f"ORB Strategy initialized: OR={or_period}min, R:R={risk_reward}, Capital=${initial_capital:,.0f}")

    def identify_opening_range(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate opening range (OR_High, OR_Low, OR_Range) for each trading day.

        Parameters
        ----------
        df : pd.DataFrame
            Intraday OHLCV data with datetime index

        Returns
        -------
        pd.DataFrame
            Input dataframe with added OR columns
        """
        logger.info(f"Calculating opening ranges for {len(df)} bars")

        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have datetime index")

        # Add date column for grouping
        df['date'] = df.index.date

        # Mark opening range bars
        df['is_opening_range'] = False
        df['OR_High'] = np.nan
        df['OR_Low'] = np.nan
        df['OR_Range'] = np.nan
        df['OR_valid'] = False

        # Process each trading day
        for date in df['date'].unique():
            day_mask = df['date'] == date
            day_data = df[day_mask].copy()

            # Find market open
            market_open = datetime.combine(
                date,
                time(config.MARKET_OPEN_HOUR, config.MARKET_OPEN_MINUTE)
            )

            # Calculate OR end time
            or_end_hour, or_end_minute = config.get_or_end_time(or_period_minutes=self.or_period)
            or_end = datetime.combine(date, time(or_end_hour, or_end_minute))

            # Mark OR period bars
            or_mask = (day_data.index >= market_open) & (day_data.index < or_end)

            if or_mask.sum() > 0:
                # Calculate OR levels
                or_high = day_data.loc[or_mask, 'High'].max()
                or_low = day_data.loc[or_mask, 'Low'].min()
                or_range = or_high - or_low

                # Calculate OR range as % of price
                or_range_pct = or_range / or_low if or_low > 0 else 0

                # Validate OR (must meet minimum range requirement)
                or_valid = or_range_pct >= config.MIN_OR_RANGE_PCT

                # Broadcast OR levels to all bars in the day
                df.loc[day_mask, 'is_opening_range'] = or_mask
                df.loc[day_mask, 'OR_High'] = or_high
                df.loc[day_mask, 'OR_Low'] = or_low
                df.loc[day_mask, 'OR_Range'] = or_range
                df.loc[day_mask, 'OR_valid'] = or_valid

                if or_valid:
                    logger.debug(f"{date}: OR {or_low:.2f}-{or_high:.2f}, Range={or_range:.2f} ({or_range_pct*100:.2f}%)")
                else:
                    logger.debug(f"{date}: OR INVALID - Range too small ({or_range_pct*100:.2f}%)")

        # Calculate OR statistics
        valid_ors = df[df['OR_valid'] & ~df['OR_Range'].isna()]
        if len(valid_ors) > 0:
            avg_or_pct = (valid_ors['OR_Range'] / valid_ors['OR_Low']).mean() * 100
            logger.info(f"Valid ORs: {len(valid_ors['date'].unique())}, Avg Range: {avg_or_pct:.2f}%")

        return df

    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators required for ORB strategy.

        Parameters
        ----------
        df : pd.DataFrame
            OHLCV data

        Returns
        -------
        pd.DataFrame
            DataFrame with added indicators
        """
        logger.info("Adding technical indicators")

        # ATR for volatility measurement
        df['ATR'] = self._calculate_atr(df, period=config.ATR_PERIOD)
        df['ATR_SMA'] = df['ATR'].rolling(window=20).mean()

        # Volume indicators
        df['Volume_SMA'] = df['Volume'].rolling(window=config.VOLUME_SMA_PERIOD).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']

        # Relative volume (current bar vs previous N bars)
        df['Relative_Volume'] = df['Volume'] / df['Volume'].rolling(window=5).mean()

        # Optional: RSI for additional filtering
        if hasattr(config, 'RSI_PERIOD'):
            df['RSI'] = self._calculate_rsi(df, period=config.RSI_PERIOD)

        # Optional: EMAs for trend filter
        if hasattr(config, 'EMA_FAST_PERIOD'):
            df['EMA_Fast'] = df['Close'].ewm(span=config.EMA_FAST_PERIOD, adjust=False).mean()
            df['EMA_Slow'] = df['Close'].ewm(span=config.EMA_SLOW_PERIOD, adjust=False).mean()

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate long/short entry signals based on ORB rules.

        Parameters
        ----------
        df : pd.DataFrame
            Data with OR levels and indicators

        Returns
        -------
        pd.DataFrame
            DataFrame with signal columns
        """
        logger.info("Generating ORB signals")

        # Initialize signal columns
        df['long_signal'] = False
        df['short_signal'] = False
        df['signal_price'] = np.nan
        df['confirmation_count'] = 0

        # Mark trading window
        df = self._mark_trading_window(df)

        # Process each trading day
        for date in df['date'].unique():
            day_mask = df['date'] == date
            day_data = df[day_mask].copy()

            if not day_data['OR_valid'].iloc[0]:
                continue  # Skip invalid ORs

            # Get OR levels
            or_high = day_data['OR_High'].iloc[0]
            or_low = day_data['OR_Low'].iloc[0]
            or_range = day_data['OR_Range'].iloc[0]

            # Add buffer to avoid false breakouts
            buffer = or_low * config.BREAKOUT_BUFFER_PCT
            long_trigger = or_high + buffer
            short_trigger = or_low - buffer

            # Track confirmation bars
            confirmation_long = 0
            confirmation_short = 0
            signal_generated_long = False
            signal_generated_short = False

            for idx in day_data.index:
                if not day_data.loc[idx, 'is_trading_window']:
                    continue

                # Long signal logic
                if not signal_generated_long and day_data.loc[idx, 'Close'] > long_trigger:
                    confirmation_long += 1
                    df.loc[idx, 'confirmation_count'] = confirmation_long

                    # Check if confirmation requirement met
                    if confirmation_long >= config.CONFIRMATION_BARS:
                        # Validate entry conditions
                        if self._validate_entry(day_data.loc[idx], 'long'):
                            df.loc[idx, 'long_signal'] = True
                            df.loc[idx, 'signal_price'] = day_data.loc[idx, 'Close']
                            signal_generated_long = True
                            logger.debug(f"{idx}: LONG signal at {day_data.loc[idx, 'Close']:.2f}")
                else:
                    confirmation_long = 0

                # Short signal logic
                if not signal_generated_short and day_data.loc[idx, 'Close'] < short_trigger:
                    confirmation_short += 1
                    df.loc[idx, 'confirmation_count'] = confirmation_short

                    # Check if confirmation requirement met
                    if confirmation_short >= config.CONFIRMATION_BARS:
                        # Validate entry conditions
                        if self._validate_entry(day_data.loc[idx], 'short'):
                            df.loc[idx, 'short_signal'] = True
                            df.loc[idx, 'signal_price'] = day_data.loc[idx, 'Close']
                            signal_generated_short = True
                            logger.debug(f"{idx}: SHORT signal at {day_data.loc[idx, 'Close']:.2f}")
                else:
                    confirmation_short = 0

                # Only one signal per day
                if signal_generated_long or signal_generated_short:
                    break

        signal_count = df['long_signal'].sum() + df['short_signal'].sum()
        logger.info(f"Generated {signal_count} signals ({df['long_signal'].sum()} long, {df['short_signal'].sum()} short)")

        return df

    def calculate_stops_targets(
        self,
        entry_price: float,
        or_range: float,
        direction: str
    ) -> Dict[str, float]:
        """
        Calculate stop loss and profit target levels.

        Parameters
        ----------
        entry_price : float
            Entry price for the trade
        or_range : float
            Opening range size
        direction : str
            'long' or 'short'

        Returns
        -------
        dict
            Dictionary with stop and target levels
        """
        if direction == 'long':
            initial_stop = entry_price - (or_range * config.INITIAL_STOP_MULTIPLIER)
            breakeven_trigger = entry_price + (or_range * config.BREAKEVEN_TRIGGER_MULTIPLIER)
            target_1 = entry_price + (or_range * config.PROFIT_TARGET_1_MULTIPLIER)
            target_2 = entry_price + (or_range * config.PROFIT_TARGET_2_MULTIPLIER)
            target_3 = entry_price + (or_range * config.PROFIT_TARGET_3_MULTIPLIER)
            trailing_distance = or_range * config.TRAILING_STOP_MULTIPLIER

        else:  # short
            initial_stop = entry_price + (or_range * config.INITIAL_STOP_MULTIPLIER)
            breakeven_trigger = entry_price - (or_range * config.BREAKEVEN_TRIGGER_MULTIPLIER)
            target_1 = entry_price - (or_range * config.PROFIT_TARGET_1_MULTIPLIER)
            target_2 = entry_price - (or_range * config.PROFIT_TARGET_2_MULTIPLIER)
            target_3 = entry_price - (or_range * config.PROFIT_TARGET_3_MULTIPLIER)
            trailing_distance = or_range * config.TRAILING_STOP_MULTIPLIER

        return {
            'initial_stop': initial_stop,
            'current_stop': initial_stop,
            'breakeven_trigger': breakeven_trigger,
            'target_1': target_1,
            'target_2': target_2,
            'target_3': target_3,
            'trailing_distance': trailing_distance,
            'stop_moved_to_be': False,
        }

    def calculate_position_size(
        self,
        capital: float,
        stop_distance: float,
        price: float,
        or_range: float,
        atr: float,
        win_rate: float = 0.45,
        avg_win_loss_ratio: float = 1.8
    ) -> int:
        """
        Calculate position size using Kelly Criterion with safety factors.

        Parameters
        ----------
        capital : float
            Current account capital
        stop_distance : float
            Distance to stop loss in dollars
        price : float
            Current price per share
        or_range : float
            Opening range size
        atr : float
            Current ATR
        win_rate : float
            Historical win rate (default 0.45)
        avg_win_loss_ratio : float
            Average win/loss ratio (default 1.8)

        Returns
        -------
        int
            Number of shares to trade
        """
        # Base Kelly fraction
        kelly_fraction = (win_rate * avg_win_loss_ratio - (1 - win_rate)) / avg_win_loss_ratio
        kelly_fraction = max(0, kelly_fraction)  # Never negative
        adjusted_kelly = kelly_fraction * config.KELLY_SAFETY_FACTOR

        # Volatility adjustment based on OR/ATR ratio
        or_atr_ratio = or_range / atr if atr > 0 else 1.0
        if or_atr_ratio > 1.5:
            volatility_adj = 0.7  # OR unusually wide - reduce position
        elif or_atr_ratio < 0.5:
            volatility_adj = 0.5  # OR unusually narrow - reduce further
        else:
            volatility_adj = 1.0

        # Calculate risk per trade
        risk_per_trade = min(adjusted_kelly, config.MAX_RISK_PER_TRADE_PCT) * volatility_adj
        risk_dollars = capital * risk_per_trade

        # Calculate shares based on stop distance
        shares = int(risk_dollars / stop_distance) if stop_distance > 0 else 0

        # Apply position size limits
        max_shares = int((capital * config.MAX_POSITION_SIZE_PCT) / price)
        min_shares = int((capital * config.MIN_POSITION_SIZE_PCT) / price)

        shares = max(min(shares, max_shares), min_shares)

        logger.debug(f"Position sizing: Kelly={kelly_fraction:.3f}, Adj={adjusted_kelly:.3f}, "
                    f"Risk=${risk_dollars:.0f}, Shares={shares}")

        return shares

    def _validate_entry(self, row: pd.Series, direction: str) -> bool:
        """
        Additional validation filters for entry signals.

        Parameters
        ----------
        row : pd.Series
            Current bar data
        direction : str
            'long' or 'short'

        Returns
        -------
        bool
            True if entry is valid
        """
        # Volume confirmation
        if row['Volume_Ratio'] < config.VOLUME_MULTIPLIER:
            logger.debug(f"Entry rejected: Low volume ratio {row['Volume_Ratio']:.2f}")
            return False

        # Relative volume check
        if row['Relative_Volume'] < 1.0:
            logger.debug(f"Entry rejected: Low relative volume {row['Relative_Volume']:.2f}")
            return False

        # ATR filter (avoid low volatility)
        if 'ATR_SMA' in row.index and row['ATR_SMA'] > 0:
            atr_ratio = row['ATR'] / row['ATR_SMA']
            if atr_ratio < config.MIN_ATR_MULTIPLIER:
                logger.debug(f"Entry rejected: Low ATR ratio {atr_ratio:.2f}")
                return False

        # Check for excessive gap
        if 'prev_close' in row.index:
            gap_pct = abs(row['Open'] - row['prev_close']) / row['prev_close']
            if gap_pct > config.MAX_GAP_PCT:
                logger.debug(f"Entry rejected: Gap too large {gap_pct*100:.2f}%")
                return False

        # Optional: Trend filter using EMAs
        if 'EMA_Fast' in row.index and 'EMA_Slow' in row.index:
            if direction == 'long' and row['EMA_Fast'] < row['EMA_Slow']:
                logger.debug("Entry rejected: EMAs not aligned for long")
                return False
            if direction == 'short' and row['EMA_Fast'] > row['EMA_Slow']:
                logger.debug("Entry rejected: EMAs not aligned for short")
                return False

        return True

    def _mark_trading_window(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Mark which bars are within the trading window.

        Parameters
        ----------
        df : pd.DataFrame
            Intraday data

        Returns
        -------
        pd.DataFrame
            DataFrame with is_trading_window column
        """
        df['is_trading_window'] = False

        windows = config.get_trading_window()
        or_end_time = time(*windows['or_end'])
        trading_end_time = time(*windows['trading_end'])

        # Mark bars in trading window (after OR, before cutoff)
        df['is_trading_window'] = (
            (df.index.time >= or_end_time) &
            (df.index.time <= trading_end_time)
        )

        return df

    @staticmethod
    def _calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high = df['High']
        low = df['Low']
        close = df['Close'].shift(1)

        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr

    @staticmethod
    def _calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def reset_daily_state(self):
        """Reset daily tracking variables (call at start of each day)."""
        self.daily_pnl = 0.0
        self.trade_count_today = {}
        logger.info("Daily state reset")

    def check_daily_loss_limit(self) -> bool:
        """
        Check if daily loss limit has been exceeded.

        Returns
        -------
        bool
            True if trading can continue, False if limit exceeded
        """
        max_loss = self.current_capital * config.MAX_DAILY_LOSS_PCT
        if self.daily_pnl < -max_loss:
            logger.warning(f"Daily loss limit exceeded: ${self.daily_pnl:.2f} < ${-max_loss:.2f}")
            return False
        return True


# Convenience function for quick testing
def test_orb_strategy(symbol: str = 'SPY', timeframe: str = '5min'):
    """
    Quick test of ORB strategy on a symbol.

    Parameters
    ----------
    symbol : str
        Symbol to test (default 'SPY')
    timeframe : str
        Timeframe to use (default '5min')
    """
    import os
    import sys

    # Add parent directory to path to import data loading functions
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    print(f"\n{'='*80}")
    print(f"Testing ORB Strategy: {symbol} ({timeframe})")
    print(f"{'='*80}\n")

    # Try to load data
    data_path = f"../../data/intraday/{timeframe}/{symbol}_intraday.csv"
    if os.path.exists(data_path):
        df = pd.read_csv(data_path, index_col=0, parse_dates=True)
        print(f"Loaded {len(df)} bars from {df.index[0]} to {df.index[-1]}")

        # Initialize strategy
        strategy = ORBStrategy()

        # Add indicators
        df = strategy.add_technical_indicators(df)

        # Identify ORs
        df = strategy.identify_opening_range(df)

        # Generate signals
        df = strategy.generate_signals(df)

        # Print summary
        print(f"\nSignals Generated:")
        print(f"  Long: {df['long_signal'].sum()}")
        print(f"  Short: {df['short_signal'].sum()}")
        print(f"  Valid ORs: {df['OR_valid'].sum()}")

        return df
    else:
        print(f"Data file not found: {data_path}")
        return None


if __name__ == '__main__':
    # Run test if executed directly
    test_orb_strategy()
