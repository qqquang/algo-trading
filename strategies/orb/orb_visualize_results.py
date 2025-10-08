"""
ORB Strategy Results Visualization
Creates equity curve and position count visualization similar to RSI2 strategy
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


def create_orb_visualization(
    trades_file='walk_forward_trades.csv',
    initial_capital=10000,
    output_file='orb_strategy_results.png'
):
    """
    Create visualization of ORB strategy results.

    Parameters
    ----------
    trades_file : str
        Path to trades CSV file
    initial_capital : float
        Starting capital
    output_file : str
        Output file name for the chart
    """

    # Load trades
    try:
        trades = pd.read_csv(trades_file)
        print(f"Loaded {len(trades)} trades from {trades_file}")
    except FileNotFoundError:
        print(f"Error: {trades_file} not found")
        return

    # Convert timestamps
    trades['entry_time'] = pd.to_datetime(trades['entry_time'])
    trades['exit_time'] = pd.to_datetime(trades['exit_time'])

    # Sort by entry time
    trades = trades.sort_values('entry_time')

    # Calculate equity curve
    trades['cumulative_pnl'] = trades['pnl'].cumsum()
    trades['equity'] = initial_capital + trades['cumulative_pnl']

    # Create date range for complete equity curve
    if len(trades) > 0:
        start_date = trades['entry_time'].min().date()
        end_date = trades['exit_time'].max().date()

        # Build complete equity curve with daily granularity
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        equity_curve = pd.DataFrame({'date': date_range})
        equity_curve['equity'] = initial_capital
        equity_curve['positions'] = 0

        # Fill in equity values based on trades
        for idx, trade in trades.iterrows():
            # Update equity from trade exit onwards
            mask = equity_curve['date'] >= pd.Timestamp(trade['exit_time'].date())
            equity_curve.loc[mask, 'equity'] = initial_capital + trade['cumulative_pnl']

        # Calculate position count for each day
        for date in equity_curve['date']:
            # Count active positions on this date
            active_count = 0
            for _, trade in trades.iterrows():
                if pd.Timestamp(trade['entry_time'].date()) <= date <= pd.Timestamp(trade['exit_time'].date()):
                    active_count += 1
            equity_curve.loc[equity_curve['date'] == date, 'positions'] = active_count

    else:
        print("No trades to visualize")
        return

    # Create the visualization
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    # Equity Curve (Top Panel)
    ax1.plot(equity_curve['date'], equity_curve['equity'],
             label='Portfolio Value', linewidth=2, color='#1f77b4')
    ax1.axhline(y=initial_capital, color='gray', linestyle='--', alpha=0.5)

    # Fill between for profit/loss
    ax1.fill_between(equity_curve['date'], initial_capital, equity_curve['equity'],
                     where=equity_curve['equity'] > initial_capital,
                     alpha=0.3, color='green', label='Profit')
    ax1.fill_between(equity_curve['date'], initial_capital, equity_curve['equity'],
                     where=equity_curve['equity'] <= initial_capital,
                     alpha=0.3, color='red', label='Loss')

    ax1.set_title('Opening Range Breakout (ORB) Strategy - Equity Curve',
                  fontsize=14, fontweight='bold')
    ax1.set_ylabel('Portfolio Value ($)', fontsize=11)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)

    # Format y-axis as currency
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    # Position Count (Bottom Panel)
    ax2.bar(equity_curve['date'], equity_curve['positions'],
            color='#1f77b4', alpha=0.6, width=1.0)
    ax2.set_title('Number of Active Positions', fontsize=12)
    ax2.set_xlabel('Date', fontsize=11)
    ax2.set_ylabel('Positions', fontsize=11)
    ax2.set_ylim(0, max(equity_curve['positions'].max() + 1, 2))
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=100, bbox_inches='tight')
    plt.close()

    print(f"\n✓ Chart saved as {output_file}")

    # Print summary statistics
    final_equity = equity_curve['equity'].iloc[-1]
    total_return = (final_equity - initial_capital) / initial_capital * 100
    max_equity = equity_curve['equity'].max()

    # Calculate drawdown
    equity_curve['peak'] = equity_curve['equity'].cummax()
    equity_curve['drawdown'] = (equity_curve['equity'] - equity_curve['peak']) / equity_curve['peak'] * 100
    max_drawdown = equity_curve['drawdown'].min()

    # Trade statistics
    winning_trades = trades[trades['pnl'] > 0]
    losing_trades = trades[trades['pnl'] <= 0]
    win_rate = len(winning_trades) / len(trades) * 100 if len(trades) > 0 else 0

    avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
    avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
    profit_factor = abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if len(losing_trades) > 0 and losing_trades['pnl'].sum() != 0 else 0

    # Calculate Sharpe ratio (simplified - using trade returns)
    if len(trades) > 1:
        trade_returns = trades['pnl_pct']
        sharpe = trade_returns.mean() / trade_returns.std() * np.sqrt(252) if trade_returns.std() > 0 else 0
    else:
        sharpe = 0

    print("\n" + "="*60)
    print("ORB STRATEGY PERFORMANCE SUMMARY")
    print("="*60)
    print(f"Initial Capital:    ${initial_capital:>12,.2f}")
    print(f"Final Equity:       ${final_equity:>12,.2f}")
    print(f"Total Return:       {total_return:>12.2f}%")
    print(f"Max Drawdown:       {max_drawdown:>12.2f}%")
    print(f"Sharpe Ratio:       {sharpe:>12.2f}")
    print("-"*60)
    print(f"Total Trades:       {len(trades):>12,}")
    print(f"Winning Trades:     {len(winning_trades):>12,}")
    print(f"Losing Trades:      {len(losing_trades):>12,}")
    print(f"Win Rate:           {win_rate:>12.1f}%")
    print(f"Profit Factor:      {profit_factor:>12.2f}")
    print(f"Avg Win:            ${avg_win:>12.2f}")
    print(f"Avg Loss:           ${avg_loss:>12.2f}")
    print(f"Avg Hold Time:      {trades['holding_time_hours'].mean():>12.1f} hours")
    print("="*60)

    return equity_curve, trades


if __name__ == "__main__":
    import os
    import sys

    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("\n" + "="*60)
    print("ORB STRATEGY RESULTS VISUALIZATION")
    print("="*60 + "\n")

    # Create visualization from walk-forward results
    equity_curve, trades = create_orb_visualization(
        trades_file='walk_forward_trades.csv',
        initial_capital=10000,
        output_file='../../results/orb_strategy_results.png'
    )

    print("\n✓ Visualization complete!")
