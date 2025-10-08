"""
RSI(2) Mean Reversion Strategy - Fixed Implementation
Following the exact rules from the research report
"""

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

class RSI2Strategy:
    """
    RSI(2) Mean Reversion Strategy - Proper Implementation

    Entry Rules (from report):
    - RSI(2) < 10 for long entry
    - Stock must be above 200 DMA (uptrend filter)
    - Enter on next open after signal

    Exit Rules:
    - Exit when RSI(2) > 70 or 80
    - OR time-based exit after 2-3 days
    - OR exit at middle Bollinger Band

    Position Sizing:
    - Fixed percentage of equity (10% per position)
    - Maximum 10 positions
    """

    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}  # {symbol: {'shares': x, 'entry_price': y, 'entry_date': z}}
        self.trades = []
        self.equity_curve = []
        self.max_positions = 10
        self.position_size = 0.1  # 10% of equity per position

    def load_data(self, symbol):
        """Load data for a symbol"""
        if symbol in ['SPY', 'QQQ', 'IWM', 'DIA'] or symbol.startswith('X'):
            filepath = f"./data/daily/etfs/{symbol}.csv"
        else:
            filepath = f"./data/daily/stocks/{symbol}.csv"

        if not os.path.exists(filepath):
            return None

        df = pd.read_csv(filepath, index_col=0, parse_dates=True)
        return df

    def calculate_signals(self, df):
        """Calculate entry and exit signals"""
        df = df.copy()

        # Entry signal: RSI(2) < 10 AND above 200 SMA
        df['entry_signal'] = (df['RSI_2'] < 10) & (df['Close'] > df['SMA_200'])

        # Exit signals
        df['exit_signal'] = (df['RSI_2'] > 70)  # Primary exit

        return df

    def backtest_single(self, symbol):
        """Backtest a single symbol"""
        df = self.load_data(symbol)
        if df is None:
            return None

        df = self.calculate_signals(df)

        # Track if we have a position
        in_position = False
        entry_price = None
        entry_date = None
        shares = 0

        for i in range(len(df)):
            date = df.index[i]
            row = df.iloc[i]

            # Skip if not enough history for indicators
            if pd.isna(row['SMA_200']) or pd.isna(row['RSI_2']):
                continue

            # EXIT LOGIC (check first if in position)
            if in_position:
                days_held = (date - entry_date).days

                # Exit conditions
                exit_now = False
                exit_reason = ''

                if row['exit_signal']:
                    exit_now = True
                    exit_reason = 'RSI > 70'
                elif days_held >= 3:
                    exit_now = True
                    exit_reason = 'Time stop (3 days)'
                elif row['Close'] >= row['BB_Middle']:
                    exit_now = True
                    exit_reason = 'Middle BB'

                if exit_now:
                    # Exit at current close
                    exit_price = row['Close']
                    profit = shares * (exit_price - entry_price)
                    return_pct = (exit_price - entry_price) / entry_price

                    self.trades.append({
                        'symbol': symbol,
                        'entry_date': entry_date,
                        'exit_date': date,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'shares': shares,
                        'profit': profit,
                        'return': return_pct,
                        'days_held': days_held,
                        'exit_reason': exit_reason
                    })

                    self.cash += shares * exit_price
                    in_position = False

            # ENTRY LOGIC (only if not in position)
            elif row['entry_signal'] and not in_position:
                # Check if we can enter (based on available cash)
                position_value = self.cash * self.position_size
                entry_price = row['Close']  # Enter at close when signal appears

                if position_value > 100:  # Minimum position size
                    shares = int(position_value / entry_price)
                    if shares > 0:
                        cost = shares * entry_price
                        if cost <= self.cash:
                            self.cash -= cost
                            in_position = True
                            entry_date = date

        # Close any remaining position
        if in_position:
            exit_price = df.iloc[-1]['Close']
            profit = shares * (exit_price - entry_price)
            self.cash += shares * exit_price

            self.trades.append({
                'symbol': symbol,
                'entry_date': entry_date,
                'exit_date': df.index[-1],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'shares': shares,
                'profit': profit,
                'return': (exit_price - entry_price) / entry_price,
                'days_held': (df.index[-1] - entry_date).days,
                'exit_reason': 'End of data'
            })

        return df

    def run_portfolio_backtest(self, symbols):
        """Run backtest on multiple symbols as a portfolio"""
        all_data = {}

        # Load all data first
        for symbol in symbols:
            df = self.load_data(symbol)
            if df is not None:
                df = self.calculate_signals(df)
                all_data[symbol] = df

        if not all_data:
            print("No data available")
            return

        # Get common date range
        all_dates = set()
        for df in all_data.values():
            all_dates.update(df.index)
        all_dates = sorted(all_dates)

        # Initialize portfolio tracking
        self.cash = self.initial_capital
        self.positions = {}
        daily_values = []

        # Process each day
        for date in all_dates:
            # Check exits first
            symbols_to_exit = []
            for symbol, position in self.positions.items():
                if symbol in all_data and date in all_data[symbol].index:
                    row = all_data[symbol].loc[date]
                    days_held = (date - position['entry_date']).days

                    # Check exit conditions
                    if (row['RSI_2'] > 70 or
                        days_held >= 3 or
                        row['Close'] >= row['BB_Middle']):
                        symbols_to_exit.append(symbol)

            # Execute exits
            for symbol in symbols_to_exit:
                position = self.positions[symbol]
                exit_price = all_data[symbol].loc[date]['Close']
                self.cash += position['shares'] * exit_price

                profit = position['shares'] * (exit_price - position['entry_price'])
                self.trades.append({
                    'symbol': symbol,
                    'entry_date': position['entry_date'],
                    'exit_date': date,
                    'entry_price': position['entry_price'],
                    'exit_price': exit_price,
                    'shares': position['shares'],
                    'profit': profit,
                    'return': (exit_price - position['entry_price']) / position['entry_price'],
                    'days_held': days_held,
                    'exit_reason': 'Signal/Time'
                })

                del self.positions[symbol]

            # Check for new entries (only if we have capacity)
            if len(self.positions) < self.max_positions:
                entry_candidates = []

                for symbol in all_data:
                    if symbol not in self.positions and date in all_data[symbol].index:
                        row = all_data[symbol].loc[date]
                        if row['entry_signal']:
                            entry_candidates.append((symbol, row['RSI_2']))

                # Sort by RSI(2) - lower is better
                entry_candidates.sort(key=lambda x: x[1])

                # Enter positions up to our limit
                for symbol, rsi in entry_candidates:
                    if len(self.positions) >= self.max_positions:
                        break

                    # Calculate position size
                    total_equity = self.calculate_total_equity(date, all_data)
                    position_value = total_equity * self.position_size
                    entry_price = all_data[symbol].loc[date]['Close']

                    shares = int(position_value / entry_price)
                    cost = shares * entry_price

                    if shares > 0 and cost <= self.cash:
                        self.cash -= cost
                        self.positions[symbol] = {
                            'shares': shares,
                            'entry_price': entry_price,
                            'entry_date': date
                        }

            # Calculate daily portfolio value
            total_value = self.calculate_total_equity(date, all_data)
            daily_values.append({
                'date': date,
                'value': total_value,
                'cash': self.cash,
                'positions': len(self.positions)
            })

        self.equity_curve = pd.DataFrame(daily_values)
        return self.equity_curve

    def calculate_total_equity(self, date, all_data):
        """Calculate total portfolio value"""
        total = self.cash

        for symbol, position in self.positions.items():
            if symbol in all_data and date in all_data[symbol].index:
                current_price = all_data[symbol].loc[date]['Close']
                total += position['shares'] * current_price

        return total

    def calculate_metrics(self):
        """Calculate performance metrics"""
        if not self.trades:
            return {"Error": "No trades executed"}

        trades_df = pd.DataFrame(self.trades)

        # Calculate metrics
        total_trades = len(trades_df)
        winning_trades = trades_df[trades_df['profit'] > 0]
        losing_trades = trades_df[trades_df['profit'] <= 0]

        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        avg_win = winning_trades['return'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['return'].mean() if len(losing_trades) > 0 else 0

        # Final portfolio value
        final_value = self.equity_curve['value'].iloc[-1] if len(self.equity_curve) > 0 else self.initial_capital
        total_return = (final_value - self.initial_capital) / self.initial_capital

        # Calculate Sharpe ratio
        if len(self.equity_curve) > 1:
            returns = self.equity_curve['value'].pct_change().dropna()
            sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        else:
            sharpe = 0

        # Max drawdown
        self.equity_curve['peak'] = self.equity_curve['value'].cummax()
        self.equity_curve['drawdown'] = (self.equity_curve['value'] - self.equity_curve['peak']) / self.equity_curve['peak']
        max_dd = self.equity_curve['drawdown'].min()

        metrics = {
            'Total Return': f"{total_return:.2%}",
            'Final Value': f"${final_value:,.2f}",
            'Total Trades': total_trades,
            'Win Rate': f"{win_rate:.1%}",
            'Avg Win': f"{avg_win:.2%}",
            'Avg Loss': f"{avg_loss:.2%}",
            'Sharpe Ratio': f"{sharpe:.2f}",
            'Max Drawdown': f"{max_dd:.2%}",
            'Avg Days Held': f"{trades_df['days_held'].mean():.1f}"
        }

        return metrics

    def plot_results(self):
        """Plot equity curve"""
        if self.equity_curve is None or len(self.equity_curve) == 0:
            return

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # Equity curve
        ax1.plot(self.equity_curve['date'], self.equity_curve['value'], label='Portfolio Value')
        ax1.axhline(y=self.initial_capital, color='gray', linestyle='--', alpha=0.5)
        ax1.fill_between(self.equity_curve['date'], self.initial_capital, self.equity_curve['value'],
                         where=self.equity_curve['value'] > self.initial_capital,
                         alpha=0.3, color='green', label='Profit')
        ax1.fill_between(self.equity_curve['date'], self.initial_capital, self.equity_curve['value'],
                         where=self.equity_curve['value'] <= self.initial_capital,
                         alpha=0.3, color='red', label='Loss')
        ax1.set_title('RSI(2) Mean Reversion Strategy - Equity Curve')
        ax1.set_ylabel('Portfolio Value ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Position count
        ax2.plot(self.equity_curve['date'], self.equity_curve['positions'], label='Active Positions')
        ax2.set_title('Number of Active Positions')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Positions')
        ax2.set_ylim(0, 11)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig('rsi2_strategy_results.png', dpi=100)
        plt.close()
        print("Chart saved as rsi2_strategy_results.png")


def main():
    """Run the strategy"""
    # Test symbols - use the most liquid for best results
    test_symbols = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
                   'META', 'TSLA', 'BRK-B', 'JPM', 'V', 'JNJ', 'WMT', 'PG']

    print("="*60)
    print("RSI(2) Mean Reversion Strategy - Portfolio Backtest")
    print("="*60)
    print(f"Testing on {len(test_symbols)} symbols")
    print(f"Initial Capital: $10,000")
    print(f"Position Size: 10% of equity")
    print(f"Max Positions: 10")
    print("-"*60)

    strategy = RSI2Strategy(initial_capital=10000)
    equity_curve = strategy.run_portfolio_backtest(test_symbols)

    if equity_curve is not None:
        metrics = strategy.calculate_metrics()
        print("\nBacktest Results:")
        print("-"*40)
        for key, value in metrics.items():
            print(f"{key:20s}: {value}")

        strategy.plot_results()

        # Save trades to CSV
        if strategy.trades:
            trades_df = pd.DataFrame(strategy.trades)
            trades_df.to_csv('rsi2_trades.csv', index=False)
            print("\nTrades saved to rsi2_trades.csv")

            # Show sample trades
            print("\nSample Trades (first 10):")
            print("-"*60)
            print(trades_df[['symbol', 'entry_date', 'exit_date', 'return', 'exit_reason']].head(10))

if __name__ == "__main__":
    main()