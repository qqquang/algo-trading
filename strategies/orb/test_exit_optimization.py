"""
Exit Strategy Optimization - Day 5
Test tighter profit targets to improve win rate and risk/reward
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from strategies.orb import ORBStrategy, orb_config
from strategies.orb.orb_backtest import ORBBacktest

def test_profit_targets(df, symbol, targets):
    """Test different profit target configurations"""

    # Save original values
    original_t1 = orb_config.PROFIT_TARGET_1_MULTIPLIER
    original_t2 = orb_config.PROFIT_TARGET_2_MULTIPLIER
    original_t3 = orb_config.PROFIT_TARGET_3_MULTIPLIER

    try:
        # Set new targets
        orb_config.PROFIT_TARGET_1_MULTIPLIER = targets[0]
        orb_config.PROFIT_TARGET_2_MULTIPLIER = targets[1]
        orb_config.PROFIT_TARGET_3_MULTIPLIER = targets[2]

        # Initialize strategy
        strategy = ORBStrategy(or_period=15, initial_capital=100000)

        # Prepare data
        df_test = df.copy()
        df_test = strategy.add_technical_indicators(df_test)
        df_test = strategy.identify_opening_range(df_test)
        df_test = strategy.generate_signals(df_test)

        # Run backtest
        backtest = ORBBacktest(strategy, initial_capital=100000)
        trades_df, metrics = backtest.run_backtest(df_test, symbol=symbol)

        return trades_df, metrics

    finally:
        # Restore original values
        orb_config.PROFIT_TARGET_1_MULTIPLIER = original_t1
        orb_config.PROFIT_TARGET_2_MULTIPLIER = original_t2
        orb_config.PROFIT_TARGET_3_MULTIPLIER = original_t3


def main():
    """Main execution"""
    print("\n" + "="*80)
    print("EXIT STRATEGY OPTIMIZATION - DAY 5")
    print("="*80)

    # Test on TSLA (best performer from Day 4)
    symbol = 'TSLA'
    data_path = f"/Users/quangnguyen/Desktop/Algo Trading/data/intraday/5min/{symbol}_extended.csv"

    print(f"\nTesting profit target variations on {symbol}")
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    print(f"Data shape: {df.shape}")
    print(f"Date range: {df.index.min()} to {df.index.max()}")

    # Define target configurations to test
    target_configs = [
        {
            'name': 'Current (Day 4)',
            'targets': (1.0, 1.5, 2.0),
            'description': 'Baseline from Day 4'
        },
        {
            'name': 'Tighter (Day 3 Recommendation)',
            'targets': (0.75, 1.25, 1.75),
            'description': 'Earlier profit taking'
        },
        {
            'name': 'Very Tight',
            'targets': (0.5, 1.0, 1.5),
            'description': 'Maximum win rate focus'
        },
        {
            'name': 'Aggressive',
            'targets': (1.25, 2.0, 2.5),
            'description': 'Larger profit focus'
        },
        {
            'name': 'Single Target',
            'targets': (0.75, 0.75, 0.75),
            'description': 'Exit all at 0.75x OR'
        },
    ]

    print(f"\nTesting {len(target_configs)} profit target configurations...")
    print("="*80)

    all_results = []

    for config in target_configs:
        print(f"\n{config['name']}: {config['targets']}")
        print(f"  {config['description']}")

        try:
            trades_df, metrics = test_profit_targets(df, symbol, config['targets'])

            # Add config info
            metrics['config_name'] = config['name']
            metrics['target_1'] = config['targets'][0]
            metrics['target_2'] = config['targets'][1]
            metrics['target_3'] = config['targets'][2]

            all_results.append(metrics)

            print(f"  Trades: {metrics['total_trades']:.0f}, "
                  f"Win Rate: {metrics['win_rate']*100:.1f}%, "
                  f"Return: {metrics['total_return_pct']:.2f}%, "
                  f"PF: {metrics['profit_factor']:.2f}")

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            continue

    # Compare results
    print("\n" + "="*80)
    print("PROFIT TARGET COMPARISON")
    print("="*80)

    if len(all_results) > 0:
        results_df = pd.DataFrame(all_results)

        # Print comparison table
        print(f"\n{'Configuration':<25} {'Targets':<15} {'Trades':<8} {'Win%':<8} {'Return%':<10} {'PF':<8} {'Sharpe':<8}")
        print("-"*95)

        for _, row in results_df.iterrows():
            targets_str = f"{row['target_1']:.2f}/{row['target_2']:.2f}/{row['target_3']:.2f}"
            print(f"{row['config_name']:<25} {targets_str:<15} "
                  f"{int(row['total_trades']):<8} "
                  f"{row['win_rate']*100:<8.1f} "
                  f"{row['total_return_pct']:<10.2f} "
                  f"{row['profit_factor']:<8.2f} "
                  f"{row['sharpe_ratio']:<8.3f}")

        # Find best configurations
        print("\n" + "="*80)
        print("BEST CONFIGURATIONS")
        print("="*80)

        best_return = results_df.loc[results_df['total_return_pct'].idxmax()]
        best_win_rate = results_df.loc[results_df['win_rate'].idxmax()]
        best_pf = results_df.loc[results_df['profit_factor'].idxmax()]
        best_sharpe = results_df.loc[results_df['sharpe_ratio'].idxmax()]

        print(f"\nBest Return: {best_return['config_name']}")
        print(f"  Targets: {best_return['target_1']:.2f}x / {best_return['target_2']:.2f}x / {best_return['target_3']:.2f}x")
        print(f"  Return: {best_return['total_return_pct']:.2f}%")
        print(f"  Win Rate: {best_return['win_rate']*100:.1f}%")
        print(f"  Profit Factor: {best_return['profit_factor']:.2f}")

        print(f"\nBest Win Rate: {best_win_rate['config_name']}")
        print(f"  Targets: {best_win_rate['target_1']:.2f}x / {best_win_rate['target_2']:.2f}x / {best_win_rate['target_3']:.2f}x")
        print(f"  Win Rate: {best_win_rate['win_rate']*100:.1f}%")
        print(f"  Return: {best_win_rate['total_return_pct']:.2f}%")
        print(f"  Profit Factor: {best_win_rate['profit_factor']:.2f}")

        print(f"\nBest Profit Factor: {best_pf['config_name']}")
        print(f"  Targets: {best_pf['target_1']:.2f}x / {best_pf['target_2']:.2f}x / {best_pf['target_3']:.2f}x")
        print(f"  Profit Factor: {best_pf['profit_factor']:.2f}")
        print(f"  Return: {best_pf['total_return_pct']:.2f}%")
        print(f"  Win Rate: {best_pf['win_rate']*100:.1f}%")

        print(f"\nBest Sharpe Ratio: {best_sharpe['config_name']}")
        print(f"  Targets: {best_sharpe['target_1']:.2f}x / {best_sharpe['target_2']:.2f}x / {best_sharpe['target_3']:.2f}x")
        print(f"  Sharpe: {best_sharpe['sharpe_ratio']:.3f}")
        print(f"  Return: {best_sharpe['total_return_pct']:.2f}%")
        print(f"  Win Rate: {best_sharpe['win_rate']*100:.1f}%")

        # Statistical analysis
        print("\n" + "="*80)
        print("STATISTICAL ANALYSIS")
        print("="*80)

        print(f"\nReturn Statistics:")
        print(f"  Mean: {results_df['total_return_pct'].mean():.2f}%")
        print(f"  Median: {results_df['total_return_pct'].median():.2f}%")
        print(f"  Std Dev: {results_df['total_return_pct'].std():.2f}%")
        print(f"  Range: {results_df['total_return_pct'].min():.2f}% to {results_df['total_return_pct'].max():.2f}%")

        print(f"\nWin Rate Statistics:")
        print(f"  Mean: {results_df['win_rate'].mean()*100:.1f}%")
        print(f"  Median: {results_df['win_rate'].median()*100:.1f}%")
        print(f"  Range: {results_df['win_rate'].min()*100:.1f}% to {results_df['win_rate'].max()*100:.1f}%")

        # Recommendations
        print("\n" + "="*80)
        print("RECOMMENDATIONS")
        print("="*80)

        # Check if tighter targets improved performance
        current_idx = results_df[results_df['config_name'] == 'Current (Day 4)'].index[0]
        tighter_idx = results_df[results_df['config_name'] == 'Tighter (Day 3 Recommendation)'].index[0]

        current_return = results_df.loc[current_idx, 'total_return_pct']
        tighter_return = results_df.loc[tighter_idx, 'total_return_pct']

        current_wr = results_df.loc[current_idx, 'win_rate']
        tighter_wr = results_df.loc[tighter_idx, 'win_rate']

        if tighter_return > current_return and tighter_wr > current_wr:
            print("\n✅ TIGHTER TARGETS IMPROVE BOTH RETURN AND WIN RATE")
            print(f"   Return improvement: {tighter_return - current_return:+.2f}%")
            print(f"   Win rate improvement: {(tighter_wr - current_wr)*100:+.1f}%")
            print(f"\n   Recommendation: Switch to {best_return['target_1']:.2f}x / {best_return['target_2']:.2f}x / {best_return['target_3']:.2f}x targets")
        elif tighter_wr > current_wr:
            print("\n⚠️  TIGHTER TARGETS IMPROVE WIN RATE BUT NOT RETURN")
            print(f"   Win rate improvement: {(tighter_wr - current_wr)*100:+.1f}%")
            print(f"   Return change: {tighter_return - current_return:+.2f}%")
            print("\n   Recommendation: Consider psychological benefits of higher win rate vs absolute return")
        else:
            print("\n❌ CURRENT TARGETS OPTIMAL")
            print(f"   Keep existing 1.0x / 1.5x / 2.0x configuration")

        # Save results
        results_df.to_csv('/Users/quangnguyen/Desktop/Algo Trading/strategies/orb/exit_optimization_results.csv', index=False)
        print("\n💾 Results saved to: exit_optimization_results.csv")

    print("\n" + "="*80)
    print("EXIT OPTIMIZATION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
