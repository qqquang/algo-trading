"""
Test Trend Filter Impact - Day 4
Compare performance with and without EMA_21 trend filter
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from strategies.orb import ORBStrategy, orb_config
from strategies.orb.orb_backtest import ORBBacktest

def test_with_trend_filter(df, use_filter=True):
    """Test strategy with trend filter enabled/disabled"""

    # Temporarily set trend filter
    original_value = orb_config.USE_TREND_FILTER
    orb_config.USE_TREND_FILTER = use_filter

    try:
        # Initialize strategy
        strategy = ORBStrategy(or_period=15, initial_capital=100000)

        # Prepare data
        df_test = df.copy()
        df_test = strategy.add_technical_indicators(df_test)
        df_test = strategy.identify_opening_range(df_test)
        df_test = strategy.generate_signals(df_test)

        # Run backtest
        backtest = ORBBacktest(strategy, initial_capital=100000)
        trades_df, metrics = backtest.run_backtest(df_test, symbol='SPY')

        return trades_df, metrics

    finally:
        # Restore original value
        orb_config.USE_TREND_FILTER = original_value


def main():
    """Main execution"""
    print("\n" + "="*80)
    print("TREND FILTER IMPACT TEST - DAY 4")
    print("="*80)
    print(f"\nComparing performance WITH and WITHOUT EMA_21 trend filter")
    print(f"Test parameters (Day 3 Extended optimized):")
    print(f"  MIN_OR_RANGE_PCT: {orb_config.MIN_OR_RANGE_PCT}")
    print(f"  VOLUME_MULTIPLIER: {orb_config.VOLUME_MULTIPLIER}")
    print(f"  CONFIRMATION_BARS: {orb_config.CONFIRMATION_BARS}")
    print(f"  INITIAL_STOP_MULTIPLIER: {orb_config.INITIAL_STOP_MULTIPLIER}")

    # Load extended data
    data_path = "/Users/quangnguyen/Desktop/Algo Trading/data/intraday/5min/SPY_extended.csv"
    print(f"\nLoading data from: {data_path}")
    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    print(f"Data shape: {df.shape}")
    print(f"Date range: {df.index.min()} to {df.index.max()}")

    # Test WITHOUT trend filter
    print("\n" + "="*80)
    print("TEST 1: WITHOUT TREND FILTER")
    print("="*80)
    trades_no_filter, metrics_no_filter = test_with_trend_filter(df, use_filter=False)

    print(f"\nResults (NO Trend Filter):")
    print(f"  Total Trades: {metrics_no_filter['total_trades']}")
    print(f"  Win Rate: {metrics_no_filter['win_rate']*100:.1f}%")
    print(f"  Total Return: {metrics_no_filter['total_return_pct']:.2f}%")
    print(f"  Sharpe Ratio: {metrics_no_filter['sharpe_ratio']:.3f}")
    print(f"  Profit Factor: {metrics_no_filter['profit_factor']:.2f}")
    print(f"  Max Drawdown: {metrics_no_filter['max_drawdown_pct']:.2f}%")

    # Test WITH trend filter
    print("\n" + "="*80)
    print("TEST 2: WITH TREND FILTER (EMA_21)")
    print("="*80)
    trades_with_filter, metrics_with_filter = test_with_trend_filter(df, use_filter=True)

    print(f"\nResults (WITH Trend Filter):")
    print(f"  Total Trades: {metrics_with_filter['total_trades']}")
    print(f"  Win Rate: {metrics_with_filter['win_rate']*100:.1f}%")
    print(f"  Total Return: {metrics_with_filter['total_return_pct']:.2f}%")
    print(f"  Sharpe Ratio: {metrics_with_filter['sharpe_ratio']:.3f}")
    print(f"  Profit Factor: {metrics_with_filter['profit_factor']:.2f}")
    print(f"  Max Drawdown: {metrics_with_filter['max_drawdown_pct']:.2f}%")

    # Compare results
    print("\n" + "="*80)
    print("COMPARISON: TREND FILTER IMPACT")
    print("="*80)

    print(f"\n{'Metric':<25} {'No Filter':<15} {'With Filter':<15} {'Change'}")
    print("-"*80)

    metrics_to_compare = [
        ('Total Trades', 'total_trades', ''),
        ('Win Rate', 'win_rate', '%'),
        ('Total Return', 'total_return_pct', '%'),
        ('Sharpe Ratio', 'sharpe_ratio', ''),
        ('Profit Factor', 'profit_factor', ''),
        ('Max Drawdown', 'max_drawdown_pct', '%'),
    ]

    for label, key, suffix in metrics_to_compare:
        val_no = metrics_no_filter[key]
        val_with = metrics_with_filter[key]

        if suffix == '%' and key != 'total_return_pct' and key != 'max_drawdown_pct':
            val_no *= 100
            val_with *= 100

        if key == 'total_trades':
            change = f"{val_with - val_no:+.0f} trades"
        elif suffix == '%':
            change = f"{val_with - val_no:+.2f}{suffix}"
        else:
            change = f"{val_with - val_no:+.3f}"

        # Format values
        if key == 'total_trades':
            val_no_str = f"{val_no:.0f}"
            val_with_str = f"{val_with:.0f}"
        elif suffix == '%':
            val_no_str = f"{val_no:.2f}%"
            val_with_str = f"{val_with:.2f}%"
        else:
            val_no_str = f"{val_no:.3f}"
            val_with_str = f"{val_with:.3f}"

        # Highlight improvement
        if key in ['win_rate', 'total_return_pct', 'sharpe_ratio', 'profit_factor']:
            improvement = "✓" if val_with > val_no else "✗"
        elif key == 'max_drawdown_pct':
            improvement = "✓" if val_with < val_no else "✗"
        elif key == 'total_trades':
            improvement = "→"  # Neutral
        else:
            improvement = ""

        print(f"{label:<25} {val_no_str:<15} {val_with_str:<15} {change} {improvement}")

    # Interpretation
    print("\n" + "="*80)
    print("INTERPRETATION")
    print("="*80)

    win_rate_change = (metrics_with_filter['win_rate'] - metrics_no_filter['win_rate']) * 100
    return_change = metrics_with_filter['total_return_pct'] - metrics_no_filter['total_return_pct']
    pf_change = metrics_with_filter['profit_factor'] - metrics_no_filter['profit_factor']

    print(f"\nTrend Filter Impact:")
    print(f"  Win Rate: {win_rate_change:+.1f} percentage points")
    print(f"  Return: {return_change:+.2f}%")
    print(f"  Profit Factor: {pf_change:+.2f}")
    print(f"  Trade Count: {metrics_with_filter['total_trades'] - metrics_no_filter['total_trades']:+.0f}")

    if win_rate_change > 5:
        print(f"\n✅ SIGNIFICANT IMPROVEMENT: Trend filter increased win rate by {win_rate_change:.1f}%")
        print("   Recommendation: KEEP trend filter enabled")
    elif win_rate_change > 0:
        print(f"\n→ SLIGHT IMPROVEMENT: Trend filter increased win rate by {win_rate_change:.1f}%")
        print("   Recommendation: Consider keeping trend filter")
    else:
        print(f"\n⚠️  NO IMPROVEMENT: Trend filter decreased win rate by {abs(win_rate_change):.1f}%")
        print("   Recommendation: Consider disabling trend filter")

    # Save comparison results
    comparison_df = pd.DataFrame({
        'Metric': [m[0] for m in metrics_to_compare],
        'Without_Filter': [metrics_no_filter[m[1]] for m in metrics_to_compare],
        'With_Filter': [metrics_with_filter[m[1]] for m in metrics_to_compare],
    })

    output_path = "/Users/quangnguyen/Desktop/Algo Trading/strategies/orb/trend_filter_comparison.csv"
    comparison_df.to_csv(output_path, index=False)
    print(f"\n💾 Comparison saved to: {output_path}")

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
