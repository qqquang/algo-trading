"""
Multi-Symbol Validation - Day 4
Test optimized ORB strategy on SPY, QQQ, and TSLA to validate robustness
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from strategies.orb import ORBStrategy
from strategies.orb.orb_backtest import ORBBacktest

def test_symbol(symbol, data_path):
    """Test strategy on a single symbol"""

    print(f"\n{'='*80}")
    print(f"TESTING {symbol}")
    print('='*80)

    # Load data
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    print(f"Data shape: {df.shape}")
    print(f"Date range: {df.index.min()} to {df.index.max()}")

    # Initialize strategy with optimized parameters
    strategy = ORBStrategy(or_period=15, initial_capital=100000)

    # Prepare data
    df_test = df.copy()
    df_test = strategy.add_technical_indicators(df_test)
    df_test = strategy.identify_opening_range(df_test)
    df_test = strategy.generate_signals(df_test)

    # Run backtest
    backtest = ORBBacktest(strategy, initial_capital=100000)
    trades_df, metrics = backtest.run_backtest(df_test, symbol=symbol)

    # Print results
    print(f"\nResults for {symbol}:")
    print(f"  Total Trades: {metrics['total_trades']:.0f}")
    print(f"  Win Rate: {metrics['win_rate']*100:.1f}%")
    print(f"  Total Return: {metrics['total_return_pct']:.2f}%")
    print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
    print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"  Max Drawdown: {metrics['max_drawdown_pct']:.2f}%")
    print(f"  Avg Win: ${metrics['avg_win']:.2f}")
    print(f"  Avg Loss: ${metrics['avg_loss']:.2f}")

    return trades_df, metrics


def main():
    """Main execution"""
    print("\n" + "="*80)
    print("MULTI-SYMBOL VALIDATION - DAY 4")
    print("="*80)
    print("\nTesting optimized ORB strategy on multiple symbols")
    print("Parameters (from Day 3 Extended optimization):")

    from strategies.orb import orb_config
    print(f"  OR_PERIOD_MINUTES: {orb_config.OR_PERIOD_MINUTES}")
    print(f"  MIN_OR_RANGE_PCT: {orb_config.MIN_OR_RANGE_PCT}")
    print(f"  VOLUME_MULTIPLIER: {orb_config.VOLUME_MULTIPLIER}")
    print(f"  CONFIRMATION_BARS: {orb_config.CONFIRMATION_BARS}")
    print(f"  INITIAL_STOP_MULTIPLIER: {orb_config.INITIAL_STOP_MULTIPLIER}")
    print(f"  USE_TREND_FILTER: {orb_config.USE_TREND_FILTER}")

    # Define symbols to test
    symbols = {
        'SPY': '/Users/quangnguyen/Desktop/Algo Trading/data/intraday/5min/SPY_extended.csv',
        'QQQ': '/Users/quangnguyen/Desktop/Algo Trading/data/intraday/5min/QQQ_extended.csv',
        'TSLA': '/Users/quangnguyen/Desktop/Algo Trading/data/intraday/5min/TSLA_extended.csv',
    }

    # Store results for all symbols
    all_metrics = {}
    all_trades = {}

    # Test each symbol
    for symbol, data_path in symbols.items():
        try:
            trades_df, metrics = test_symbol(symbol, data_path)
            all_metrics[symbol] = metrics
            all_trades[symbol] = trades_df
        except Exception as e:
            print(f"\n❌ Error testing {symbol}: {str(e)}")
            import traceback
            traceback.print_exc()

    # Compare results across symbols
    print("\n" + "="*80)
    print("CROSS-SYMBOL COMPARISON")
    print("="*80)

    if len(all_metrics) > 0:
        comparison_df = pd.DataFrame(all_metrics).T

        print(f"\n{'Symbol':<10} {'Trades':<10} {'Win Rate':<12} {'Return':<12} {'Sharpe':<10} {'PF':<10} {'Max DD':<10}")
        print("-"*80)

        for symbol in all_metrics.keys():
            m = all_metrics[symbol]
            print(f"{symbol:<10} "
                  f"{m['total_trades']:<10.0f} "
                  f"{m['win_rate']*100:<12.1f}% "
                  f"{m['total_return_pct']:<12.2f}% "
                  f"{m['sharpe_ratio']:<10.3f} "
                  f"{m['profit_factor']:<10.2f} "
                  f"{m['max_drawdown_pct']:<10.2f}%")

        # Calculate average metrics
        print("\n" + "-"*80)
        avg_trades = sum(m['total_trades'] for m in all_metrics.values()) / len(all_metrics)
        avg_win_rate = sum(m['win_rate'] for m in all_metrics.values()) / len(all_metrics)
        avg_return = sum(m['total_return_pct'] for m in all_metrics.values()) / len(all_metrics)
        avg_sharpe = sum(m['sharpe_ratio'] for m in all_metrics.values()) / len(all_metrics)
        avg_pf = sum(m['profit_factor'] for m in all_metrics.values()) / len(all_metrics)
        avg_dd = sum(m['max_drawdown_pct'] for m in all_metrics.values()) / len(all_metrics)

        print(f"{'AVERAGE':<10} "
              f"{avg_trades:<10.1f} "
              f"{avg_win_rate*100:<12.1f}% "
              f"{avg_return:<12.2f}% "
              f"{avg_sharpe:<10.3f} "
              f"{avg_pf:<10.2f} "
              f"{avg_dd:<10.2f}%")

        # Analysis
        print("\n" + "="*80)
        print("ANALYSIS")
        print("="*80)

        # Find best and worst performing symbols
        best_symbol = max(all_metrics.keys(), key=lambda s: all_metrics[s]['total_return_pct'])
        worst_symbol = min(all_metrics.keys(), key=lambda s: all_metrics[s]['total_return_pct'])

        print(f"\nBest Performing Symbol: {best_symbol}")
        print(f"  Return: {all_metrics[best_symbol]['total_return_pct']:.2f}%")
        print(f"  Win Rate: {all_metrics[best_symbol]['win_rate']*100:.1f}%")
        print(f"  Sharpe: {all_metrics[best_symbol]['sharpe_ratio']:.3f}")

        print(f"\nWorst Performing Symbol: {worst_symbol}")
        print(f"  Return: {all_metrics[worst_symbol]['total_return_pct']:.2f}%")
        print(f"  Win Rate: {all_metrics[worst_symbol]['win_rate']*100:.1f}%")
        print(f"  Sharpe: {all_metrics[worst_symbol]['sharpe_ratio']:.3f}")

        # Consistency check
        print(f"\nConsistency Metrics:")
        print(f"  Win Rate Range: {min(m['win_rate'] for m in all_metrics.values())*100:.1f}% - {max(m['win_rate'] for m in all_metrics.values())*100:.1f}%")
        print(f"  Return Range: {min(m['total_return_pct'] for m in all_metrics.values()):.2f}% - {max(m['total_return_pct'] for m in all_metrics.values()):.2f}%")
        print(f"  Sharpe Range: {min(m['sharpe_ratio'] for m in all_metrics.values()):.3f} - {max(m['sharpe_ratio'] for m in all_metrics.values()):.3f}")

        # Overall assessment
        print("\n" + "="*80)
        print("OVERALL ASSESSMENT")
        print("="*80)

        profitable_symbols = sum(1 for m in all_metrics.values() if m['total_return_pct'] > 0)
        win_rate_above_40 = sum(1 for m in all_metrics.values() if m['win_rate'] > 0.40)
        pf_above_1 = sum(1 for m in all_metrics.values() if m['profit_factor'] > 1.0)

        print(f"\nProfitable Symbols: {profitable_symbols}/{len(all_metrics)}")
        print(f"Win Rate > 40%: {win_rate_above_40}/{len(all_metrics)}")
        print(f"Profit Factor > 1.0: {pf_above_1}/{len(all_metrics)}")

        if avg_win_rate > 0.40 and avg_pf > 1.0:
            print("\n✅ STRATEGY VALIDATED: Strong performance across symbols")
            print("   Recommendation: Proceed to live testing preparation")
        elif profitable_symbols >= 2:
            print("\n⚠️  MIXED RESULTS: Some symbols profitable, others not")
            print("   Recommendation: Consider symbol-specific parameter tuning")
        else:
            print("\n❌ POOR PERFORMANCE: Strategy not profitable across symbols")
            print("   Recommendation: Fundamental strategy redesign needed")

        # Save comparison results
        comparison_df.to_csv('/Users/quangnguyen/Desktop/Algo Trading/strategies/orb/multi_symbol_comparison.csv')
        print("\n💾 Comparison saved to: multi_symbol_comparison.csv")

        # Save all trades combined
        if all_trades:
            combined_trades = pd.concat([df.assign(symbol=symbol) for symbol, df in all_trades.items() if len(df) > 0])
            combined_trades.to_csv('/Users/quangnguyen/Desktop/Algo Trading/strategies/orb/multi_symbol_trades.csv')
            print("💾 All trades saved to: multi_symbol_trades.csv")

    print("\n" + "="*80)
    print("MULTI-SYMBOL VALIDATION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
