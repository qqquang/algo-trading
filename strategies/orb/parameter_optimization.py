"""
Parameter Optimization for ORB Strategy - Day 3

Grid search optimization to find optimal parameters:
- MIN_OR_RANGE_PCT
- VOLUME_MULTIPLIER
- CONFIRMATION_BARS
- INITIAL_STOP_MULTIPLIER

Uses Sharpe Ratio as primary metric (not just return)
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from itertools import product

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from strategies.orb import ORBStrategy, orb_config
from strategies.orb.orb_backtest import ORBBacktest

# Setup logging
logging.basicConfig(
    level=logging.WARNING,  # Suppress INFO logs during optimization
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def run_single_backtest(df, params):
    """Run backtest with specific parameters."""
    # Temporarily modify config
    original_values = {}
    for key, value in params.items():
        original_values[key] = getattr(orb_config, key)
        setattr(orb_config, key, value)

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

        return metrics

    finally:
        # Restore original config
        for key, value in original_values.items():
            setattr(orb_config, key, value)


def parameter_grid_search(df):
    """
    Grid search across parameter combinations.
    """
    logger.info("="*80)
    logger.info("PARAMETER GRID SEARCH OPTIMIZATION")
    logger.info("="*80)

    # Define parameter grid
    param_grid = {
        'MIN_OR_RANGE_PCT': [0.0005, 0.001, 0.0015, 0.002],  # 0.05%, 0.1%, 0.15%, 0.2%
        'VOLUME_MULTIPLIER': [1.0, 1.2, 1.5],
        'CONFIRMATION_BARS': [1, 2],
        'INITIAL_STOP_MULTIPLIER': [0.5, 0.75, 1.0],
    }

    # Calculate total combinations
    total_combinations = np.prod([len(v) for v in param_grid.values()])
    logger.info(f"Testing {total_combinations} parameter combinations...")
    logger.info(f"Parameters to optimize: {list(param_grid.keys())}\n")

    # Store results
    results = []

    # Generate all combinations
    keys = list(param_grid.keys())
    values = list(param_grid.values())

    for i, combination in enumerate(product(*values), 1):
        params = dict(zip(keys, combination))

        logger.info(f"[{i}/{total_combinations}] Testing: {params}")

        try:
            metrics = run_single_backtest(df, params)

            # Add parameters to metrics
            result = {**params, **metrics}
            results.append(result)

            # Log key metrics
            logger.info(f"  → Trades: {metrics['total_trades']}, "
                       f"Win Rate: {metrics['win_rate']*100:.1f}%, "
                       f"Sharpe: {metrics['sharpe_ratio']:.2f}, "
                       f"Profit Factor: {metrics['profit_factor']:.2f}")

        except Exception as e:
            logger.warning(f"  → ERROR: {str(e)}")
            continue

    # Convert to DataFrame
    results_df = pd.DataFrame(results)

    return results_df


def analyze_optimization_results(results_df):
    """Analyze and rank parameter combinations."""
    logger.info("\n" + "="*80)
    logger.info("OPTIMIZATION RESULTS ANALYSIS")
    logger.info("="*80)

    # Filter out combinations with too few trades
    min_trades = 10
    valid_results = results_df[results_df['total_trades'] >= min_trades].copy()

    logger.info(f"\nTotal combinations tested: {len(results_df)}")
    logger.info(f"Valid combinations (≥{min_trades} trades): {len(valid_results)}")

    if len(valid_results) == 0:
        logger.warning("No combinations produced enough trades!")
        return None

    # Rank by multiple criteria
    logger.info("\n" + "-"*80)
    logger.info("TOP 10 BY SHARPE RATIO")
    logger.info("-"*80)

    top_sharpe = valid_results.nlargest(10, 'sharpe_ratio')
    for idx, row in top_sharpe.iterrows():
        logger.info(f"\nRank {idx+1}:")
        logger.info(f"  Parameters:")
        logger.info(f"    MIN_OR_RANGE_PCT: {row['MIN_OR_RANGE_PCT']:.4f} ({row['MIN_OR_RANGE_PCT']*100:.2f}%)")
        logger.info(f"    VOLUME_MULTIPLIER: {row['VOLUME_MULTIPLIER']:.1f}x")
        logger.info(f"    CONFIRMATION_BARS: {int(row['CONFIRMATION_BARS'])}")
        logger.info(f"    INITIAL_STOP_MULTIPLIER: {row['INITIAL_STOP_MULTIPLIER']:.2f}x")
        logger.info(f"  Performance:")
        logger.info(f"    Sharpe Ratio: {row['sharpe_ratio']:.3f}")
        logger.info(f"    Total Trades: {int(row['total_trades'])}")
        logger.info(f"    Win Rate: {row['win_rate']*100:.1f}%")
        logger.info(f"    Profit Factor: {row['profit_factor']:.2f}")
        logger.info(f"    Total Return: {row['total_return_pct']:.2f}%")
        logger.info(f"    Max Drawdown: {row['max_drawdown_pct']:.2f}%")

    logger.info("\n" + "-"*80)
    logger.info("TOP 5 BY PROFIT FACTOR (among profitable strategies)")
    logger.info("-"*80)

    profitable = valid_results[valid_results['profit_factor'] > 1.0]
    if len(profitable) > 0:
        top_pf = profitable.nlargest(5, 'profit_factor')
        for idx, row in top_pf.iterrows():
            logger.info(f"\nRank {idx+1}:")
            logger.info(f"  MIN_OR_RANGE_PCT: {row['MIN_OR_RANGE_PCT']:.4f}, "
                       f"VOLUME_MULT: {row['VOLUME_MULTIPLIER']:.1f}x, "
                       f"CONF_BARS: {int(row['CONFIRMATION_BARS'])}, "
                       f"STOP: {row['INITIAL_STOP_MULTIPLIER']:.2f}x")
            logger.info(f"  Profit Factor: {row['profit_factor']:.2f}, "
                       f"Win Rate: {row['win_rate']*100:.1f}%, "
                       f"Trades: {int(row['total_trades'])}")
    else:
        logger.warning("No profitable parameter combinations found!")

    logger.info("\n" + "-"*80)
    logger.info("TOP 5 BY WIN RATE")
    logger.info("-"*80)

    top_wr = valid_results.nlargest(5, 'win_rate')
    for idx, row in top_wr.iterrows():
        logger.info(f"\nRank {idx+1}:")
        logger.info(f"  MIN_OR_RANGE_PCT: {row['MIN_OR_RANGE_PCT']:.4f}, "
                   f"VOLUME_MULT: {row['VOLUME_MULTIPLIER']:.1f}x, "
                   f"CONF_BARS: {int(row['CONFIRMATION_BARS'])}, "
                   f"STOP: {row['INITIAL_STOP_MULTIPLIER']:.2f}x")
        logger.info(f"  Win Rate: {row['win_rate']*100:.1f}%, "
                   f"Profit Factor: {row['profit_factor']:.2f}, "
                   f"Trades: {int(row['total_trades'])}")

    # Best overall (composite score)
    logger.info("\n" + "-"*80)
    logger.info("RECOMMENDED PARAMETERS (Composite Score)")
    logger.info("-"*80)

    # Calculate composite score
    valid_results['composite_score'] = (
        valid_results['sharpe_ratio'] * 0.4 +
        valid_results['profit_factor'] * 0.3 +
        valid_results['win_rate'] * 0.2 +
        (1 - valid_results['max_drawdown_pct'] / 100) * 0.1
    )

    best = valid_results.nlargest(1, 'composite_score').iloc[0]
    logger.info(f"\nBest Parameter Set:")
    logger.info(f"  MIN_OR_RANGE_PCT: {best['MIN_OR_RANGE_PCT']:.4f} ({best['MIN_OR_RANGE_PCT']*100:.2f}%)")
    logger.info(f"  VOLUME_MULTIPLIER: {best['VOLUME_MULTIPLIER']:.1f}x")
    logger.info(f"  CONFIRMATION_BARS: {int(best['CONFIRMATION_BARS'])}")
    logger.info(f"  INITIAL_STOP_MULTIPLIER: {best['INITIAL_STOP_MULTIPLIER']:.2f}x")
    logger.info(f"\nPerformance:")
    logger.info(f"  Sharpe Ratio: {best['sharpe_ratio']:.3f}")
    logger.info(f"  Profit Factor: {best['profit_factor']:.2f}")
    logger.info(f"  Win Rate: {best['win_rate']*100:.1f}%")
    logger.info(f"  Total Return: {best['total_return_pct']:.2f}%")
    logger.info(f"  Max Drawdown: {best['max_drawdown_pct']:.2f}%")
    logger.info(f"  Total Trades: {int(best['total_trades'])}")
    logger.info(f"  Composite Score: {best['composite_score']:.3f}")

    return results_df, best


def save_optimization_results(results_df, output_path):
    """Save optimization results to CSV."""
    results_df.to_csv(output_path, index=False)
    logger.info(f"\nOptimization results saved to: {output_path}")


def main():
    """Main optimization execution."""
    logger.info("="*80)
    logger.info("ORB STRATEGY - PARAMETER OPTIMIZATION (DAY 3)")
    logger.info("="*80)

    # Load extended data (60 days instead of 1 month)
    data_path = "/Users/quangnguyen/Desktop/Algo Trading/data/intraday/5min/SPY_extended.csv"
    logger.info(f"\nLoading EXTENDED data from: {data_path}")
    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    logger.info(f"Data shape: {df.shape}")
    logger.info(f"Date range: {df.index.min()} to {df.index.max()}")
    trading_days = len(pd.Series(df.index.date).unique())
    logger.info(f"Trading days: {trading_days}")

    # Run optimization
    start_time = datetime.now()
    results_df = parameter_grid_search(df)
    end_time = datetime.now()

    logger.info(f"\nOptimization completed in {(end_time - start_time).total_seconds():.1f} seconds")

    # Analyze results
    results_df, best_params = analyze_optimization_results(results_df)

    # Save results to new file for extended data
    output_path = "/Users/quangnguyen/Desktop/Algo Trading/strategies/orb/optimization_results_extended.csv"
    save_optimization_results(results_df, output_path)

    logger.info("\n" + "="*80)
    logger.info("OPTIMIZATION COMPLETE")
    logger.info("="*80)


if __name__ == "__main__":
    main()
