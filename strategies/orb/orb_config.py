"""
ORB Strategy Configuration

This file contains all configurable parameters for the Opening Range Breakout strategy.
Modify these parameters to test different variations without changing core logic.
"""

from typing import Dict, List, Tuple

# ============================================================================
# OPENING RANGE PARAMETERS
# ============================================================================

# Opening range period in minutes (15 or 30 recommended)
OR_PERIOD_MINUTES: int = 15

# Market open time (EST) - Regular trading hours
MARKET_OPEN_HOUR: int = 9
MARKET_OPEN_MINUTE: int = 30

# ============================================================================
# ENTRY PARAMETERS
# ============================================================================

# Buffer above/below OR to avoid false breakouts (% of price)
BREAKOUT_BUFFER_PCT: float = 0.0005  # 0.05%

# Number of bars price must stay above/below OR for confirmation
CONFIRMATION_BARS: int = 2

# Volume multiplier for entry confirmation
VOLUME_MULTIPLIER: float = 1.5

# Minimum ATR multiplier vs average (avoid low volatility days)
MIN_ATR_MULTIPLIER: float = 0.5

# Minimum OR range as % of price (avoid tiny ranges)
MIN_OR_RANGE_PCT: float = 0.002  # 0.2%

# Maximum gap size as % (skip high gap days)
MAX_GAP_PCT: float = 0.01  # 1%

# ============================================================================
# EXIT PARAMETERS
# ============================================================================

# Initial stop loss as multiple of OR range
INITIAL_STOP_MULTIPLIER: float = 0.75

# Breakeven move trigger (move stop to BE after this much profit)
BREAKEVEN_TRIGGER_MULTIPLIER: float = 0.5  # Move to BE after 0.5x OR profit

# Profit targets as multiples of OR range (for scaled exits)
PROFIT_TARGET_1_MULTIPLIER: float = 1.0   # 50% position
PROFIT_TARGET_2_MULTIPLIER: float = 1.5   # 25% position
PROFIT_TARGET_3_MULTIPLIER: float = 2.0   # Final 25% position

# Position scaling percentages
SCALE_OUT_PCT_1: float = 0.50  # 50% at target 1
SCALE_OUT_PCT_2: float = 0.25  # 25% at target 2
SCALE_OUT_PCT_3: float = 0.25  # 25% at target 3

# Trailing stop multiplier (after reaching target 1)
TRAILING_STOP_MULTIPLIER: float = 0.3

# Time stop - close all positions by this time (EST)
TIME_STOP_HOUR: int = 15
TIME_STOP_MINUTE: int = 55

# Trading window end (no new trades after this time)
TRADING_WINDOW_END_HOUR: int = 15
TRADING_WINDOW_END_MINUTE: int = 30

# ============================================================================
# POSITION SIZING PARAMETERS
# ============================================================================

# Maximum risk per trade as % of capital
MAX_RISK_PER_TRADE_PCT: float = 0.02  # 2%

# Maximum position size as % of capital
MAX_POSITION_SIZE_PCT: float = 0.15  # 15%

# Minimum position size as % of capital
MIN_POSITION_SIZE_PCT: float = 0.005  # 0.5%

# Kelly fraction safety factor (use only 25% of Kelly suggestion)
KELLY_SAFETY_FACTOR: float = 0.25

# ============================================================================
# RISK MANAGEMENT PARAMETERS
# ============================================================================

# Maximum daily loss as % of capital (stop trading if exceeded)
MAX_DAILY_LOSS_PCT: float = 0.05  # 5%

# Maximum number of open positions
MAX_OPEN_POSITIONS: int = 3

# Maximum correlation between positions (avoid concentrated risk)
MAX_CORRELATION: float = 0.80

# Maximum trades per symbol per day
MAX_TRADES_PER_SYMBOL_PER_DAY: int = 1

# Drawdown management thresholds
DRAWDOWN_THRESHOLDS: Dict[str, Tuple[float, float]] = {
    # (drawdown_pct, position_size_multiplier)
    'normal': (0.03, 1.0),      # < 3% DD: Full size
    'caution': (0.05, 0.75),    # 3-5% DD: Reduce to 75%
    'warning': (0.08, 0.50),    # 5-8% DD: Reduce to 50%
    'danger': (0.10, 0.25),     # 8-10% DD: Reduce to 25%
    'stop': (0.10, 0.0),        # > 10% DD: Stop trading
}

# ============================================================================
# MARKET REGIME PARAMETERS
# ============================================================================

# Risk adjustments based on market conditions
REGIME_RISK_MULTIPLIERS: Dict[str, float] = {
    'high_volatility': 0.5,
    'trending': 1.2,
    'choppy': 0.3,
    'low_volume': 0.5,
    'friday': 0.7,
    'fomc_day': 0.4,
    'earnings_season': 0.6,
}

# ATR spike threshold for volatility exit (tighten stops if exceeded)
ATR_SPIKE_THRESHOLD: float = 2.0
ATR_SPIKE_STOP_MULTIPLIER: float = 0.5

# ============================================================================
# TECHNICAL INDICATOR PARAMETERS
# ============================================================================

# ATR period for volatility calculation
ATR_PERIOD: int = 14

# Volume SMA period for volume comparison
VOLUME_SMA_PERIOD: int = 20

# RSI period (optional filter)
RSI_PERIOD: int = 14

# EMA periods for trend filter (optional)
EMA_FAST_PERIOD: int = 9
EMA_SLOW_PERIOD: int = 21

# ADX period for trend strength (optional)
ADX_PERIOD: int = 14
MIN_ADX_FOR_TREND: int = 25

# ============================================================================
# DATA PARAMETERS
# ============================================================================

# Supported timeframes for ORB
SUPPORTED_TIMEFRAMES: List[str] = ['1min', '5min', '15min', '30min']

# Default timeframe for backtesting
DEFAULT_TIMEFRAME: str = '5min'

# Symbols for testing (in priority order)
TEST_SYMBOLS: List[str] = ['SPY', 'QQQ', 'TSLA', 'NVDA', 'AAPL']

# ============================================================================
# BACKTESTING PARAMETERS
# ============================================================================

# Initial capital for backtesting
INITIAL_CAPITAL: float = 100000.0

# Commission per trade (dollar amount)
COMMISSION_PER_TRADE: float = 1.0

# Slippage as % of price
SLIPPAGE_PCT: float = 0.0005  # 0.05% = 5 basis points

# ============================================================================
# LOGGING AND MONITORING
# ============================================================================

# Enable detailed logging
VERBOSE_LOGGING: bool = True

# Log file path (relative to strategy folder)
LOG_FILE: str = 'orb_strategy.log'

# Save trade details
SAVE_TRADE_DETAILS: bool = True

# ============================================================================
# MACHINE LEARNING PARAMETERS (Optional - for future enhancement)
# ============================================================================

# Enable ML-based entry filter
ENABLE_ML_FILTER: bool = False

# ML prediction threshold (only take trades with >60% success probability)
ML_PROBABILITY_THRESHOLD: float = 0.60

# ML model path
ML_MODEL_PATH: str = 'models/orb_classifier.pkl'

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_or_end_time(market_open_hour: int = MARKET_OPEN_HOUR,
                    market_open_minute: int = MARKET_OPEN_MINUTE,
                    or_period_minutes: int = OR_PERIOD_MINUTES) -> Tuple[int, int]:
    """
    Calculate the end time of the opening range.

    Returns:
        Tuple of (hour, minute) when opening range ends
    """
    total_minutes = market_open_hour * 60 + market_open_minute + or_period_minutes
    end_hour = total_minutes // 60
    end_minute = total_minutes % 60
    return (end_hour, end_minute)


def get_trading_window() -> Dict[str, Tuple[int, int]]:
    """
    Get the full trading window boundaries.

    Returns:
        Dict with 'or_start', 'or_end', 'trading_end', 'time_stop' times
    """
    or_end = get_or_end_time()

    return {
        'or_start': (MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE),
        'or_end': or_end,
        'trading_end': (TRADING_WINDOW_END_HOUR, TRADING_WINDOW_END_MINUTE),
        'time_stop': (TIME_STOP_HOUR, TIME_STOP_MINUTE),
    }


def validate_config() -> bool:
    """
    Validate configuration parameters for consistency.

    Returns:
        True if config is valid, raises ValueError otherwise
    """
    # Check OR period is reasonable
    if OR_PERIOD_MINUTES not in [15, 30]:
        raise ValueError(f"OR_PERIOD_MINUTES should be 15 or 30, got {OR_PERIOD_MINUTES}")

    # Check profit targets are ascending
    if not (PROFIT_TARGET_1_MULTIPLIER < PROFIT_TARGET_2_MULTIPLIER < PROFIT_TARGET_3_MULTIPLIER):
        raise ValueError("Profit targets must be in ascending order")

    # Check scale out percentages sum to 1.0
    total_scale = SCALE_OUT_PCT_1 + SCALE_OUT_PCT_2 + SCALE_OUT_PCT_3
    if abs(total_scale - 1.0) > 0.01:
        raise ValueError(f"Scale out percentages must sum to 1.0, got {total_scale}")

    # Check time windows make sense
    or_end = get_or_end_time()
    if or_end[0] > TRADING_WINDOW_END_HOUR or \
       (or_end[0] == TRADING_WINDOW_END_HOUR and or_end[1] >= TRADING_WINDOW_END_MINUTE):
        raise ValueError("OR end time must be before trading window end")

    if TRADING_WINDOW_END_HOUR > TIME_STOP_HOUR or \
       (TRADING_WINDOW_END_HOUR == TIME_STOP_HOUR and TRADING_WINDOW_END_MINUTE >= TIME_STOP_MINUTE):
        raise ValueError("Trading window end must be before time stop")

    # Check position sizing makes sense
    if MAX_POSITION_SIZE_PCT <= MIN_POSITION_SIZE_PCT:
        raise ValueError("MAX_POSITION_SIZE_PCT must be greater than MIN_POSITION_SIZE_PCT")

    if MAX_RISK_PER_TRADE_PCT > MAX_POSITION_SIZE_PCT:
        raise ValueError("MAX_RISK_PER_TRADE_PCT should not exceed MAX_POSITION_SIZE_PCT")

    return True


# Validate configuration on import
if __name__ != '__main__':
    validate_config()


# Print configuration summary if run directly
if __name__ == '__main__':
    print("=" * 80)
    print("ORB STRATEGY CONFIGURATION SUMMARY")
    print("=" * 80)
    print(f"\nOpening Range: {OR_PERIOD_MINUTES} minutes ({MARKET_OPEN_HOUR}:{MARKET_OPEN_MINUTE:02d} - {get_or_end_time()[0]}:{get_or_end_time()[1]:02d})")
    print(f"Trading Window: {get_or_end_time()[0]}:{get_or_end_time()[1]:02d} - {TRADING_WINDOW_END_HOUR}:{TRADING_WINDOW_END_MINUTE:02d}")
    print(f"Time Stop: {TIME_STOP_HOUR}:{TIME_STOP_MINUTE:02d}")

    print(f"\nEntry Parameters:")
    print(f"  - Breakout Buffer: {BREAKOUT_BUFFER_PCT * 100:.2f}%")
    print(f"  - Confirmation Bars: {CONFIRMATION_BARS}")
    print(f"  - Volume Multiplier: {VOLUME_MULTIPLIER}x")
    print(f"  - Min OR Range: {MIN_OR_RANGE_PCT * 100:.2f}%")

    print(f"\nExit Parameters:")
    print(f"  - Initial Stop: {INITIAL_STOP_MULTIPLIER}x OR")
    print(f"  - Breakeven Trigger: {BREAKEVEN_TRIGGER_MULTIPLIER}x OR")
    print(f"  - Profit Targets: {PROFIT_TARGET_1_MULTIPLIER}x ({SCALE_OUT_PCT_1*100:.0f}%), " \
          f"{PROFIT_TARGET_2_MULTIPLIER}x ({SCALE_OUT_PCT_2*100:.0f}%), " \
          f"{PROFIT_TARGET_3_MULTIPLIER}x ({SCALE_OUT_PCT_3*100:.0f}%)")
    print(f"  - Trailing Stop: {TRAILING_STOP_MULTIPLIER}x OR")

    print(f"\nPosition Sizing:")
    print(f"  - Max Risk Per Trade: {MAX_RISK_PER_TRADE_PCT * 100:.1f}%")
    print(f"  - Max Position Size: {MAX_POSITION_SIZE_PCT * 100:.1f}%")
    print(f"  - Kelly Safety Factor: {KELLY_SAFETY_FACTOR * 100:.0f}%")

    print(f"\nRisk Management:")
    print(f"  - Max Daily Loss: {MAX_DAILY_LOSS_PCT * 100:.1f}%")
    print(f"  - Max Open Positions: {MAX_OPEN_POSITIONS}")
    print(f"  - Max Trades Per Symbol/Day: {MAX_TRADES_PER_SYMBOL_PER_DAY}")

    print(f"\nBacktesting:")
    print(f"  - Initial Capital: ${INITIAL_CAPITAL:,.0f}")
    print(f"  - Commission: ${COMMISSION_PER_TRADE:.2f} per trade")
    print(f"  - Slippage: {SLIPPAGE_PCT * 100:.2f}%")

    print("\n" + "=" * 80)
    print("Configuration validation: PASSED")
    print("=" * 80)
