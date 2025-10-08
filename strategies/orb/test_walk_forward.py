"""
Walk-Forward Validation - Day 4
Test strategy robustness using rolling time windows
Train on 20 days, test on 5 days, roll forward
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from strategies.orb import ORBStrategy
from strategies.orb.orb_backtest import ORBBacktest

def split_into_windows(df, train_days=20, test_days=5):
    """Split data into rolling train/test windows"""

    # Get unique trading days
    df_copy = df.copy()
    df_copy['date'] = df_copy.index.date
    unique_dates = sorted(df_copy['date'].unique())

    print(f"\nTotal trading days: {len(unique_dates)}")
    print(f"Window config: Train={train_days} days, Test={test_days} days")

    windows = []
    current_idx = 0
    window_num = 1

    while current_idx + train_days + test_days <= len(unique_dates):
        # Define train and test date ranges
        train_start_date = unique_dates[current_idx]
        train_end_date = unique_dates[current_idx + train_days - 1]
        test_start_date = unique_dates[current_idx + train_days]
        test_end_date = unique_dates[current_idx + train_days + test_days - 1]

        # Extract data for this window
        train_mask = (df_copy['date'] >= train_start_date) & (df_copy['date'] <= train_end_date)
        test_mask = (df_copy['date'] >= test_start_date) & (df_copy['date'] <= test_end_date)

        train_df = df[train_mask].copy()
        test_df = df[test_mask].copy()

        windows.append({
            'window_num': window_num,
            'train_start': train_start_date,
            'train_end': train_end_date,
            'test_start': test_start_date,
            'test_end': test_end_date,
            'train_df': train_df,
            'test_df': test_df
        })

        # Roll forward by test_days
        current_idx += test_days
        window_num += 1

    print(f"Created {len(windows)} walk-forward windows\n")
    return windows


def test_window(window, symbol):
    """Test a single walk-forward window"""

    print(f"Window {window['window_num']}: Train {window['train_start']} to {window['train_end']}, "
          f"Test {window['test_start']} to {window['test_end']}")

    # For this implementation, we'll use fixed parameters (from Day 3 optimization)
    # In a full implementation, you could re-optimize on each train window
    strategy = ORBStrategy(or_period=15, initial_capital=100000)

    # Prepare test data
    df_test = window['test_df'].copy()
    df_test = strategy.add_technical_indicators(df_test)
    df_test = strategy.identify_opening_range(df_test)
    df_test = strategy.generate_signals(df_test)

    # Run backtest on test period only
    backtest = ORBBacktest(strategy, initial_capital=100000)
    trades_df, metrics = backtest.run_backtest(df_test, symbol=symbol)

    print(f"  Trades: {metrics['total_trades']:.0f}, "
          f"Win Rate: {metrics['win_rate']*100:.1f}%, "
          f"Return: {metrics['total_return_pct']:.2f}%, "
          f"PF: {metrics['profit_factor']:.2f}")

    return metrics, trades_df


def main():
    """Main execution"""
    print("\n" + "="*80)
    print("WALK-FORWARD VALIDATION - DAY 4")
    print("="*80)

    from strategies.orb import orb_config
    print(f"\nUsing optimized parameters:")
    print(f"  MIN_OR_RANGE_PCT: {orb_config.MIN_OR_RANGE_PCT}")
    print(f"  VOLUME_MULTIPLIER: {orb_config.VOLUME_MULTIPLIER}")
    print(f"  CONFIRMATION_BARS: {orb_config.CONFIRMATION_BARS}")
    print(f"  INITIAL_STOP_MULTIPLIER: {orb_config.INITIAL_STOP_MULTIPLIER}")
    print(f"  USE_TREND_FILTER: {orb_config.USE_TREND_FILTER}")

    # Test on SPY (most liquid, representative)
    symbol = 'SPY'
    data_path = f"/Users/quangnguyen/Desktop/Algo Trading/data/intraday/5min/{symbol}_extended.csv"

    print(f"\nLoading {symbol} data from: {data_path}")
    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    print(f"Data shape: {df.shape}")
    print(f"Date range: {df.index.min()} to {df.index.max()}")

    # Create walk-forward windows (20 train, 5 test)
    windows = split_into_windows(df, train_days=20, test_days=5)

    # Test each window
    all_window_metrics = []
    all_window_trades = []

    print("="*80)
    print("TESTING WINDOWS")
    print("="*80 + "\n")

    for window in windows:
        try:
            metrics, trades = test_window(window, symbol)

            # Add window info to metrics
            metrics['window_num'] = window['window_num']
            metrics['test_start'] = window['test_start']
            metrics['test_end'] = window['test_end']

            all_window_metrics.append(metrics)

            if len(trades) > 0:
                trades['window_num'] = window['window_num']
                all_window_trades.append(trades)

        except Exception as e:
            print(f"  ❌ Error in window {window['window_num']}: {str(e)}")
            continue

    # Aggregate results
    print("\n" + "="*80)
    print("WALK-FORWARD RESULTS SUMMARY")
    print("="*80)

    if len(all_window_metrics) > 0:
        results_df = pd.DataFrame(all_window_metrics)

        # Print per-window results
        print(f"\n{'Window':<10} {'Test Period':<25} {'Trades':<8} {'Win%':<8} {'Return%':<10} {'PF':<8}")
        print("-"*80)

        for _, row in results_df.iterrows():
            period = f"{row['test_start']} to {row['test_end']}"
            print(f"{int(row['window_num']):<10} {str(period):<25} "
                  f"{int(row['total_trades']):<8} "
                  f"{row['win_rate']*100:<8.1f} "
                  f"{row['total_return_pct']:<10.2f} "
                  f"{row['profit_factor']:<8.2f}")

        # Calculate aggregate statistics
        print("\n" + "="*80)
        print("AGGREGATE STATISTICS")
        print("="*80)

        total_trades = results_df['total_trades'].sum()
        total_winning = results_df['winning_trades'].sum()
        total_losing = results_df['losing_trades'].sum()
        overall_win_rate = total_winning / total_trades if total_trades > 0 else 0

        avg_return = results_df['total_return_pct'].mean()
        median_return = results_df['total_return_pct'].median()
        std_return = results_df['total_return_pct'].std()

        avg_pf = results_df['profit_factor'].mean()
        avg_sharpe = results_df['sharpe_ratio'].mean()

        profitable_windows = (results_df['total_return_pct'] > 0).sum()
        total_windows = len(results_df)

        print(f"\nTotal Windows: {total_windows}")
        print(f"Profitable Windows: {profitable_windows} ({profitable_windows/total_windows*100:.1f}%)")
        print(f"\nTotal Trades: {int(total_trades)}")
        print(f"Overall Win Rate: {overall_win_rate*100:.1f}%")
        print(f"\nAvg Return per Window: {avg_return:.2f}%")
        print(f"Median Return per Window: {median_return:.2f}%")
        print(f"Std Dev of Returns: {std_return:.2f}%")
        print(f"\nAvg Profit Factor: {avg_pf:.2f}")
        print(f"Avg Sharpe Ratio: {avg_sharpe:.3f}")

        # Consistency metrics
        print(f"\nConsistency Metrics:")
        print(f"  Return Range: {results_df['total_return_pct'].min():.2f}% to {results_df['total_return_pct'].max():.2f}%")
        print(f"  Win Rate Range: {results_df['win_rate'].min()*100:.1f}% to {results_df['win_rate'].max()*100:.1f}%")
        print(f"  PF Range: {results_df['profit_factor'].min():.2f} to {results_df['profit_factor'].max():.2f}")

        # Assessment
        print("\n" + "="*80)
        print("ROBUSTNESS ASSESSMENT")
        print("="*80)

        if profitable_windows / total_windows >= 0.60 and overall_win_rate >= 0.40:
            print("\n✅ ROBUST STRATEGY: Consistent performance across time periods")
            print("   Recommendation: Strategy shows good out-of-sample generalization")
        elif profitable_windows / total_windows >= 0.50:
            print("\n⚠️  MODERATE ROBUSTNESS: Mixed results across time periods")
            print("   Recommendation: Consider additional filters or regime detection")
        else:
            print("\n❌ POOR ROBUSTNESS: Inconsistent performance across time periods")
            print("   Recommendation: Strategy may be overfit to specific market conditions")

        # Save results
        results_df.to_csv('/Users/quangnguyen/Desktop/Algo Trading/strategies/orb/walk_forward_results.csv', index=False)
        print("\n💾 Results saved to: walk_forward_results.csv")

        if all_window_trades:
            combined_trades = pd.concat(all_window_trades)
            combined_trades.to_csv('/Users/quangnguyen/Desktop/Algo Trading/strategies/orb/walk_forward_trades.csv')
            print("💾 All trades saved to: walk_forward_trades.csv")

    print("\n" + "="*80)
    print("WALK-FORWARD VALIDATION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
