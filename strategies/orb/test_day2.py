"""
Day 2 Testing Script - ORB Strategy on Real Data

Tests:
1. Load and validate SPY 5-min data
2. Test opening range calculation
3. Verify signal generation
4. Run preliminary backtest
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, time
import logging

# Add parent directory to path to import strategy
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from strategies.orb import ORBStrategy, orb_config
from strategies.orb.orb_backtest import ORBBacktest

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_and_validate_data(filepath: str) -> pd.DataFrame:
    """Load and validate 5-min data."""
    logger.info(f"Loading data from {filepath}")

    # Load data
    df = pd.read_csv(filepath, index_col=0, parse_dates=True)

    # Basic validation
    logger.info(f"Data shape: {df.shape}")
    logger.info(f"Date range: {df.index.min()} to {df.index.max()}")
    logger.info(f"Columns: {df.columns.tolist()}")

    # Check for required columns
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Check for missing values
    missing_pct = (df.isnull().sum() / len(df) * 100).round(2)
    logger.info(f"\nMissing values:\n{missing_pct[missing_pct > 0]}")

    # Check for duplicate timestamps
    duplicates = df.index.duplicated().sum()
    logger.info(f"Duplicate timestamps: {duplicates}")

    # Sort by timestamp
    df = df.sort_index()

    # Basic stats
    logger.info(f"\nBasic statistics:")
    logger.info(f"Average daily volume: {df.groupby(df.index.date)['Volume'].sum().mean():,.0f}")
    logger.info(f"Price range: ${df['Low'].min():.2f} - ${df['High'].max():.2f}")

    # Check for data gaps
    unique_dates = df.index.date
    unique_dates = pd.Series(unique_dates).unique()
    logger.info(f"Total trading days: {len(unique_dates)}")

    # Sample data
    logger.info(f"\nFirst 3 bars:\n{df.head(3)}")
    logger.info(f"\nLast 3 bars:\n{df.tail(3)}")

    return df


def test_opening_range(df: pd.DataFrame, strategy: ORBStrategy) -> pd.DataFrame:
    """Test opening range calculation."""
    logger.info("\n" + "="*60)
    logger.info("TESTING OPENING RANGE CALCULATION")
    logger.info("="*60)

    # Calculate opening ranges
    df = strategy.identify_opening_range(df)

    # Check results
    or_calculated = df['OR_High'].notna().sum()
    or_valid = df['OR_valid'].sum()
    logger.info(f"Opening ranges calculated: {or_calculated} bars")
    logger.info(f"Valid opening ranges: {or_valid} bars")

    # Show sample opening ranges
    or_days = df[df['OR_valid']].copy()
    or_days['date'] = or_days.index.date
    or_samples = or_days.groupby('date').first()[['OR_High', 'OR_Low', 'OR_Range']].head(10)

    logger.info(f"\nSample opening ranges (first 10 days):")
    for date, row in or_samples.iterrows():
        or_pct = (row['OR_Range'] / row['OR_Low']) * 100
        logger.info(f"{date}: High=${row['OR_High']:.2f}, Low=${row['OR_Low']:.2f}, "
                   f"Range=${row['OR_Range']:.2f} ({or_pct:.2f}%)")

    # Statistics
    valid_or_df = df[df['OR_valid']].copy()
    or_ranges_by_day = valid_or_df.groupby(valid_or_df.index.date)['OR_Range'].first()
    logger.info(f"\nOR Range statistics:")
    logger.info(f"Average OR range: ${or_ranges_by_day.mean():.2f}")
    logger.info(f"Min OR range: ${or_ranges_by_day.min():.2f}")
    logger.info(f"Max OR range: ${or_ranges_by_day.max():.2f}")
    logger.info(f"Std OR range: ${or_ranges_by_day.std():.2f}")

    return df


def test_signal_generation(df: pd.DataFrame, strategy: ORBStrategy) -> pd.DataFrame:
    """Test signal generation."""
    logger.info("\n" + "="*60)
    logger.info("TESTING SIGNAL GENERATION")
    logger.info("="*60)

    # Add technical indicators
    df = strategy.add_technical_indicators(df)

    # Generate signals
    df = strategy.generate_signals(df)

    # Count signals
    long_signals = df['long_signal'].sum()
    short_signals = df['short_signal'].sum()
    total_signals = long_signals + short_signals

    logger.info(f"Long signals: {long_signals}")
    logger.info(f"Short signals: {short_signals}")
    logger.info(f"Total signals: {total_signals}")

    # Signals per day
    trading_days = len(pd.Series(df.index.date).unique())
    signals_per_day = total_signals / trading_days if trading_days > 0 else 0
    logger.info(f"Average signals per day: {signals_per_day:.2f}")

    # Show sample signals
    signal_bars = df[(df['long_signal']) | (df['short_signal'])].head(10)
    if len(signal_bars) > 0:
        logger.info(f"\nFirst {len(signal_bars)} signals:")
        for idx, row in signal_bars.iterrows():
            direction = "LONG" if row['long_signal'] else "SHORT"
            logger.info(f"{idx} - {direction}: Close=${row['Close']:.2f}, "
                       f"OR_High=${row['OR_High']:.2f}, OR_Low=${row['OR_Low']:.2f}, "
                       f"Volume={row['Volume']:,.0f}")
    else:
        logger.warning("No signals generated!")

    return df


def run_preliminary_backtest(df: pd.DataFrame, strategy: ORBStrategy) -> tuple:
    """Run preliminary backtest."""
    logger.info("\n" + "="*60)
    logger.info("RUNNING PRELIMINARY BACKTEST")
    logger.info("="*60)

    # Initialize backtest
    backtest = ORBBacktest(strategy, initial_capital=100000)

    # Run backtest
    trades_df, metrics = backtest.run_backtest(df, symbol='SPY')

    # Display results
    logger.info(f"\n{'='*60}")
    logger.info("BACKTEST RESULTS")
    logger.info(f"{'='*60}")

    logger.info(f"\nTrade Statistics:")
    logger.info(f"Total trades: {metrics['total_trades']}")
    logger.info(f"Winning trades: {metrics['winning_trades']}")
    logger.info(f"Losing trades: {metrics['losing_trades']}")
    logger.info(f"Win rate: {metrics['win_rate']*100:.2f}%")

    logger.info(f"\nReturn Metrics:")
    logger.info(f"Total P&L: ${metrics['total_pnl']:,.2f}")
    logger.info(f"Total return: {metrics['total_return_pct']:.2f}%")
    logger.info(f"Average win: ${metrics['avg_win']:,.2f}")
    logger.info(f"Average loss: ${metrics['avg_loss']:,.2f}")
    logger.info(f"Largest win: ${metrics['largest_win']:,.2f}")
    logger.info(f"Largest loss: ${metrics['largest_loss']:,.2f}")
    logger.info(f"Profit factor: {metrics['profit_factor']:.2f}")

    logger.info(f"\nRisk Metrics:")
    logger.info(f"Sharpe ratio: {metrics['sharpe_ratio']:.2f}")
    logger.info(f"Max drawdown: {metrics['max_drawdown_pct']:.2f}%")
    logger.info(f"Average R-multiple: {metrics['avg_r_multiple']:.2f}")

    logger.info(f"\nStrategy Metrics:")
    logger.info(f"Average holding time: {metrics.get('avg_holding_time_hours', 0):.1f} hours")
    logger.info(f"Average OR range: ${metrics.get('avg_or_range', 0):.2f}")
    logger.info(f"Initial capital: ${metrics['initial_capital']:,.2f}")
    logger.info(f"Final capital: ${metrics['final_capital']:,.2f}")

    # Show sample trades
    if len(trades_df) > 0:
        logger.info(f"\nFirst 5 trades:")
        logger.info(trades_df[['entry_time', 'direction', 'entry_price', 'exit_price',
                              'shares', 'pnl', 'r_multiple', 'exit_reason']].head(5).to_string())

        logger.info(f"\nLast 5 trades:")
        logger.info(trades_df[['entry_time', 'direction', 'entry_price', 'exit_price',
                              'shares', 'pnl', 'r_multiple', 'exit_reason']].tail(5).to_string())

    return trades_df, metrics, backtest


def analyze_results(trades_df: pd.DataFrame, metrics: dict):
    """Analyze backtest results and identify issues."""
    logger.info("\n" + "="*60)
    logger.info("ANALYSIS & FINDINGS")
    logger.info("="*60)

    if len(trades_df) == 0:
        logger.warning("No trades generated - possible issues:")
        logger.warning("1. OR validation may be too strict (min range requirement)")
        logger.warning("2. Volume filter may be filtering out all signals")
        logger.warning("3. ATR filter may be too restrictive")
        logger.warning("4. Trading window may not align with data")
        return

    # Exit reason distribution
    logger.info("\nExit reason distribution:")
    exit_counts = trades_df['exit_reason'].value_counts()
    for reason, count in exit_counts.items():
        pct = (count / len(trades_df)) * 100
        logger.info(f"{reason}: {count} ({pct:.1f}%)")

    # Direction distribution
    logger.info("\nDirection distribution:")
    direction_counts = trades_df['direction'].value_counts()
    for direction, count in direction_counts.items():
        pct = (count / len(trades_df)) * 100
        logger.info(f"{direction}: {count} ({pct:.1f}%)")

    # Win/loss by direction
    logger.info("\nPerformance by direction:")
    for direction in trades_df['direction'].unique():
        dir_trades = trades_df[trades_df['direction'] == direction]
        dir_wins = len(dir_trades[dir_trades['pnl'] > 0])
        dir_win_rate = (dir_wins / len(dir_trades)) * 100
        dir_pnl = dir_trades['pnl'].sum()
        logger.info(f"{direction}: Win rate={dir_win_rate:.1f}%, Total P&L=${dir_pnl:,.2f}")

    # Recommendations
    logger.info("\nRecommendations:")

    if metrics['total_trades'] < 10:
        logger.info("⚠️  Very few trades - consider:")
        logger.info("   - Reducing minimum OR range requirement")
        logger.info("   - Lowering volume multiplier threshold")
        logger.info("   - Testing on longer time period")

    if metrics['win_rate'] < 0.40:
        logger.info("⚠️  Low win rate - consider:")
        logger.info("   - Tightening entry filters (volume, ATR)")
        logger.info("   - Adding trend filter (EMA alignment)")
        logger.info("   - Increasing confirmation bars")

    if metrics['win_rate'] > 0.60:
        logger.info("✅ High win rate - good signal quality")

    if metrics['profit_factor'] < 1.0:
        logger.info("⚠️  Profit factor < 1.0 (losing strategy)")
    elif metrics['profit_factor'] < 1.5:
        logger.info("⚠️  Profit factor below target (1.5+)")
    else:
        logger.info("✅ Profit factor meets target")

    if metrics['sharpe_ratio'] < 1.0:
        logger.info("⚠️  Low Sharpe ratio - high volatility relative to returns")
    elif metrics['sharpe_ratio'] > 1.5:
        logger.info("✅ Excellent Sharpe ratio")

    if metrics['max_drawdown_pct'] > 15:
        logger.info("⚠️  Drawdown exceeds target (15%)")
    else:
        logger.info("✅ Drawdown within acceptable range")


def main():
    """Main test execution."""
    logger.info("="*60)
    logger.info("ORB STRATEGY - DAY 2 TESTING")
    logger.info("="*60)

    # Configuration - use 5-min data for ORB strategy
    data_path = "/Users/quangnguyen/Desktop/Algo Trading/data/intraday/5min/SPY.csv"

    try:
        # Step 1: Load and validate data
        df = load_and_validate_data(data_path)

        # Step 2: Initialize strategy
        logger.info("\nInitializing ORB Strategy...")
        strategy = ORBStrategy(or_period=15, initial_capital=100000)
        logger.info(f"Strategy initialized: OR period = {strategy.or_period} minutes")

        # Step 3: Test opening range calculation
        df = test_opening_range(df, strategy)

        # Step 4: Test signal generation
        df = test_signal_generation(df, strategy)

        # Step 5: Run preliminary backtest
        trades_df, metrics, backtest = run_preliminary_backtest(df, strategy)

        # Step 6: Analyze results
        analyze_results(trades_df, metrics)

        # Generate report
        logger.info("\nGenerating backtest report...")
        report_path = "/Users/quangnguyen/Desktop/Algo Trading/strategies/orb/day2_backtest_results.md"
        report = backtest.generate_report(save_path=report_path)
        logger.info(f"Report saved to: {report_path}")

        logger.info("\n" + "="*60)
        logger.info("DAY 2 TESTING COMPLETE")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"Error during testing: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
