"""
RSI(2) Mean Reversion Backtest
Based on the #2 most profitable strategy from the research report
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

class RSI2MeanReversionBacktest:
    """
    Equity Mean Reversion Strategy using RSI(2) and Bollinger Bands

    Entry Rules:
    - Long when RSI(2) < 10 or price < Lower Bollinger Band
    - Stock must be above 200-day SMA (long-term uptrend)
    - No earnings within 2 days (simplified: we'll skip this for now)

    Exit Rules:
    - Exit when RSI(2) > 70 or at middle Bollinger Band
    - Time stop: 3 days maximum hold

    Position Sizing:
    - Fixed fraction: 1% risk per trade
    - Volatility-based sizing using ATR
    """

    def __init__(self, symbol, capital=10000):
        self.symbol = symbol
        self.initial_capital = capital
        self.capital = capital
        self.positions = []
        self.trades = []
        self.equity_curve = []

    def load_data(self):
        """Load preprocessed data from CSV"""
        # Determine file path based on symbol category
        if self.symbol in ['SPY', 'QQQ', 'IWM', 'DIA', 'XLF', 'XLK', 'XLE',
                          'XLV', 'XLI', 'XLP', 'XLU', 'XLB', 'XLY', 'XLRE',
                          'TLT', 'GLD', 'HYG', 'LQD']:
            filepath = f"./data/daily/etfs/{self.symbol}.csv"
        else:
            filepath = f"./data/daily/stocks/{self.symbol}.csv"

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Data file not found: {filepath}")

        # Load data
        df = pd.read_csv(filepath, index_col=0, parse_dates=True)

        # Ensure we have all required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume',
                        'RSI_2', 'RSI_14', 'BB_Lower', 'BB_Middle',
                        'BB_Upper', 'SMA_200', 'ATR']

        for col in required_cols:
            if col not in df.columns:
                print(f"Warning: {col} not found in data")

        return df

    def generate_signals(self, df):
        """Generate buy and sell signals based on RSI(2) mean reversion"""
        df = df.copy()

        # Long Entry Conditions
        df['long_signal'] = (
            (df['RSI_2'] < 10) |  # RSI(2) oversold
            (df['Close'] < df['BB_Lower'])  # Below lower Bollinger Band
        ) & (
            df['Close'] > df['SMA_200']  # Above 200-day SMA (uptrend filter)
        )

        # Exit Conditions
        df['exit_signal'] = (
            (df['RSI_2'] > 70) |  # RSI(2) overbought
            (df['Close'] > df['BB_Middle'])  # Above middle Bollinger Band
        )

        return df

    def backtest(self):
        """Run the backtest"""
        df = self.load_data()
        df = self.generate_signals(df)

        position = None
        entry_date = None
        entry_price = None
        shares = 0

        for date, row in df.iterrows():
            # Skip if data not ready (need 200 days for SMA)
            if pd.isna(row['SMA_200']):
                continue

            # Track equity
            current_value = self.capital
            if position:
                current_value = self.capital + (shares * row['Close'] - shares * entry_price)
            self.equity_curve.append({
                'date': date,
                'equity': current_value,
                'in_position': position is not None
            })

            # Check for exit if in position
            if position:
                days_held = (date - entry_date).days

                # Exit conditions
                if row['exit_signal'] or days_held >= 3:
                    exit_price = row['Open']  # Exit on next open
                    profit = shares * (exit_price - entry_price)
                    self.capital += profit

                    # Record trade
                    self.trades.append({
                        'entry_date': entry_date,
                        'exit_date': date,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'shares': shares,
                        'profit': profit,
                        'return': (exit_price - entry_price) / entry_price,
                        'days_held': days_held,
                        'exit_reason': 'signal' if row['exit_signal'] else 'time_stop'
                    })

                    position = None
                    entry_date = None
                    shares = 0

            # Check for entry if not in position
            elif row['long_signal'] and not position:
                entry_date = date
                entry_price = row['Open']  # Enter on next open

                # Position sizing based on ATR
                risk_per_trade = self.capital * 0.01  # 1% risk per trade
                stop_distance = row['ATR'] * 1.5  # Stop at 1.5 ATR
                shares = int(risk_per_trade / stop_distance)

                # Ensure we don't exceed capital
                max_shares = int(self.capital / entry_price)
                shares = min(shares, max_shares)

                if shares > 0:
                    position = 'long'

        # Close any open position at end
        if position:
            exit_price = df.iloc[-1]['Close']
            profit = shares * (exit_price - entry_price)
            self.capital += profit

            self.trades.append({
                'entry_date': entry_date,
                'exit_date': df.index[-1],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'shares': shares,
                'profit': profit,
                'return': (exit_price - entry_price) / entry_price,
                'days_held': (df.index[-1] - entry_date).days,
                'exit_reason': 'end_of_data'
            })

    def calculate_metrics(self):
        """Calculate performance metrics"""
        if not self.trades:
            print("No trades executed")
            return {}

        trades_df = pd.DataFrame(self.trades)
        equity_df = pd.DataFrame(self.equity_curve)

        # Basic metrics
        total_return = (self.capital - self.initial_capital) / self.initial_capital
        num_trades = len(trades_df)

        # Win rate
        winning_trades = trades_df[trades_df['profit'] > 0]
        win_rate = len(winning_trades) / num_trades if num_trades > 0 else 0

        # Average returns
        avg_return = trades_df['return'].mean()
        avg_win = winning_trades['return'].mean() if len(winning_trades) > 0 else 0
        avg_loss = trades_df[trades_df['profit'] <= 0]['return'].mean()

        # Risk/Reward
        risk_reward = abs(avg_win / avg_loss) if avg_loss != 0 else 0

        # Profit Factor
        total_wins = winning_trades['profit'].sum() if len(winning_trades) > 0 else 0
        total_losses = abs(trades_df[trades_df['profit'] <= 0]['profit'].sum())
        profit_factor = total_wins / total_losses if total_losses > 0 else 0

        # Max Drawdown
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak']
        max_drawdown = equity_df['drawdown'].min()

        # Sharpe Ratio (simplified - using daily returns)
        equity_df['returns'] = equity_df['equity'].pct_change()
        sharpe = equity_df['returns'].mean() / equity_df['returns'].std() * np.sqrt(252) if equity_df['returns'].std() > 0 else 0

        # Average holding period
        avg_hold = trades_df['days_held'].mean()

        metrics = {
            'Symbol': self.symbol,
            'Total Return': f"{total_return:.2%}",
            'Number of Trades': num_trades,
            'Win Rate': f"{win_rate:.2%}",
            'Avg Return per Trade': f"{avg_return:.2%}",
            'Avg Winning Trade': f"{avg_win:.2%}",
            'Avg Losing Trade': f"{avg_loss:.2%}",
            'Risk/Reward Ratio': f"{risk_reward:.2f}",
            'Profit Factor': f"{profit_factor:.2f}",
            'Max Drawdown': f"{max_drawdown:.2%}",
            'Sharpe Ratio': f"{sharpe:.2f}",
            'Avg Holding Period': f"{avg_hold:.1f} days",
            'Final Capital': f"${self.capital:,.2f}"
        }

        return metrics

    def plot_results(self):
        """Plot equity curve and trade markers"""
        if not self.equity_curve:
            print("No data to plot")
            return

        equity_df = pd.DataFrame(self.equity_curve)
        trades_df = pd.DataFrame(self.trades)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # Equity curve
        ax1.plot(equity_df['date'], equity_df['equity'], label='Equity Curve')
        ax1.axhline(y=self.initial_capital, color='gray', linestyle='--', alpha=0.5)
        ax1.fill_between(equity_df['date'], self.initial_capital, equity_df['equity'],
                         where=equity_df['equity']>self.initial_capital, alpha=0.3, color='green')
        ax1.fill_between(equity_df['date'], self.initial_capital, equity_df['equity'],
                         where=equity_df['equity']<=self.initial_capital, alpha=0.3, color='red')
        ax1.set_title(f'{self.symbol} - RSI(2) Mean Reversion Equity Curve')
        ax1.set_ylabel('Portfolio Value ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Trade distribution
        if len(trades_df) > 0:
            returns = trades_df['return'] * 100
            colors = ['green' if r > 0 else 'red' for r in returns]
            ax2.bar(range(len(returns)), returns, color=colors, alpha=0.6)
            ax2.axhline(y=0, color='black', linewidth=0.5)
            ax2.set_title('Trade Returns Distribution')
            ax2.set_xlabel('Trade Number')
            ax2.set_ylabel('Return (%)')
            ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(f'{self.symbol}_rsi2_backtest.png', dpi=100)
        plt.close()  # Close instead of show to avoid blocking

def run_backtest_suite():
    """Run backtest on multiple symbols and compare results"""

    # Priority symbols to test
    test_symbols = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']

    results = []

    print("="*60)
    print("RSI(2) Mean Reversion Backtest Results")
    print("="*60)

    for symbol in test_symbols:
        print(f"\nTesting {symbol}...")
        try:
            backtest = RSI2MeanReversionBacktest(symbol, capital=10000)
            backtest.backtest()
            metrics = backtest.calculate_metrics()

            # Print individual results
            print("-"*40)
            for key, value in metrics.items():
                print(f"{key:20s}: {value}")

            # Save plot
            backtest.plot_results()

            results.append(metrics)

        except Exception as e:
            print(f"Error testing {symbol}: {str(e)}")

    # Create summary DataFrame
    if results:
        summary_df = pd.DataFrame(results)
        summary_df.to_csv('rsi2_backtest_results.csv', index=False)
        print("\n" + "="*60)
        print("Results saved to rsi2_backtest_results.csv")
        print("="*60)

    return results

if __name__ == "__main__":
    # Run single backtest
    print("Starting RSI(2) Mean Reversion Backtest on SPY...")
    spy_backtest = RSI2MeanReversionBacktest('SPY', capital=10000)
    spy_backtest.backtest()
    metrics = spy_backtest.calculate_metrics()

    print("\n" + "="*50)
    print("SPY Backtest Results:")
    print("="*50)
    for key, value in metrics.items():
        print(f"{key:20s}: {value}")

    spy_backtest.plot_results()

    # Uncomment to run full suite
    # run_backtest_suite()