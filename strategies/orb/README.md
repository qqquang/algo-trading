## Opening Range Breakout (ORB) Strategy

### Overview

This directory contains a complete implementation of the Opening Range Breakout (ORB) trading strategy, designed for intraday momentum trading on liquid symbols like SPY, QQQ, and TSLA.

### Strategy Description

The ORB strategy identifies breakouts from the first 15-30 minutes of trading (the "opening range") and trades the momentum continuation. The strategy includes:

- **15-minute opening range** identification
- **Volume confirmation** filters (1.5x average volume)
- **2-bar confirmation** to avoid false breakouts
- **Scaled exits** at multiple profit targets (1x, 1.5x, 2x OR range)
- **Dynamic stop management** (moves to breakeven after 0.5x profit)
- **Kelly Criterion position sizing** with volatility adjustment

### Files

- **`orb_config.py`**: All strategy parameters and configuration
- **`orb_strategy.py`**: Core strategy logic (signal generation, position sizing)
- **`orb_backtest.py`**: Backtesting engine with performance metrics
- **`__init__.py`**: Package initialization
- **`README.md`**: This file

### Key Features

#### Entry Rules
1. Price breaks above OR_High + 0.05% buffer (long) or below OR_Low - 0.05% (short)
2. Price must stay above/below for 2 bars (confirmation)
3. Volume > 1.5x average volume
4. Current ATR > 0.5x average ATR (avoid low volatility)
5. OR range > 0.2% of price (minimum range requirement)
6. Trading window: 9:45 AM - 3:30 PM EST

#### Exit Rules
1. **Initial stop loss**: 0.75x OR range from entry
2. **Breakeven move**: Stop moves to entry after 0.5x profit
3. **Scaled exits**:
   - 50% at 1.0x OR range (Target 1)
   - 25% at 1.5x OR range (Target 2)
   - 25% at 2.0x OR range (Target 3)
4. **Trailing stop**: 0.3x OR range after reaching Target 1
5. **Time stop**: All positions closed at 3:55 PM EST

#### Risk Management
- Maximum risk per trade: 2% of capital
- Maximum position size: 15% of capital
- Daily loss limit: 5% of capital
- Kelly Criterion sizing with 25% safety factor
- Volatility-based position adjustment (OR/ATR ratio)

### Configuration

All parameters can be modified in `orb_config.py`:

```python
# Key parameters
OR_PERIOD_MINUTES = 15              # Opening range period
BREAKOUT_BUFFER_PCT = 0.0005        # 0.05% buffer
CONFIRMATION_BARS = 2                # 2-bar confirmation
VOLUME_MULTIPLIER = 1.5             # Volume confirmation
PROFIT_TARGET_1_MULTIPLIER = 1.0    # First target
PROFIT_TARGET_2_MULTIPLIER = 1.5    # Second target
PROFIT_TARGET_3_MULTIPLIER = 2.0    # Final target
```

### Usage

#### Test Configuration
```bash
cd strategies/orb
python3 orb_config.py
```

This will validate and print the configuration summary.

#### Run Strategy Test
```python
from strategies.orb import ORBStrategy
import pandas as pd

# Load data
df = pd.read_csv('../../data/intraday/5min/SPY_intraday.csv',
                 index_col=0, parse_dates=True)

# Initialize strategy
strategy = ORBStrategy(or_period=15, initial_capital=100000)

# Add technical indicators
df = strategy.add_technical_indicators(df)

# Identify opening ranges
df = strategy.identify_opening_range(df)

# Generate signals
df = strategy.generate_signals(df)

# Check signals
print(f"Long signals: {df['long_signal'].sum()}")
print(f"Short signals: {df['short_signal'].sum()}")
```

#### Run Backtest
```python
from strategies.orb import ORBStrategy
from strategies.orb.orb_backtest import ORBBacktest
import pandas as pd

# Load and prepare data
df = pd.read_csv('../../data/intraday/5min/SPY_intraday.csv',
                 index_col=0, parse_dates=True)

# Initialize strategy
strategy = ORBStrategy(or_period=15)
df = strategy.add_technical_indicators(df)
df = strategy.identify_opening_range(df)
df = strategy.generate_signals(df)

# Run backtest
backtest = ORBBacktest(strategy, initial_capital=100000)
trades_df, metrics = backtest.run_backtest(df, symbol='SPY')

# Generate report
report = backtest.generate_report(save_path='orb_results.md')
print(report)

# Analyze trades
print(f"\nTotal trades: {len(trades_df)}")
print(f"Win rate: {metrics['win_rate']*100:.1f}%")
print(f"Profit factor: {metrics['profit_factor']:.2f}")
print(f"Total return: {metrics['total_return_pct']:.2f}%")
```

### Expected Performance

Based on research and the enhanced plan:

- **Win Rate**: 40-55% (target: 45%)
- **Average R/R**: 1.3-2.0 (target: 1.8)
- **Sharpe Ratio**: > 1.5
- **Max Drawdown**: < 15%
- **Profit Factor**: > 1.5

### Next Steps (Day 2-5)

#### Day 2: Data Preparation & Core Testing
- [ ] Load and validate 5-min data for SPY
- [ ] Test opening range calculation on real data
- [ ] Verify signal generation logic
- [ ] Test basic entry/exit mechanics

#### Day 3: Backtesting
- [ ] Run first backtest on SPY 5-min
- [ ] Debug and refine based on results
- [ ] Test on QQQ and TSLA
- [ ] Compare results across symbols

#### Day 4: Optimization
- [ ] Parameter grid search (OR period, targets, stops)
- [ ] Filter optimization (volume, ATR thresholds)
- [ ] Walk-forward validation
- [ ] Multi-timeframe comparison (5-min vs 15-min)

#### Day 5: Analysis & Documentation
- [ ] Generate performance report
- [ ] Create visualizations (equity curve, drawdown, trade distribution)
- [ ] Document findings and insights
- [ ] Compare to RSI(2) strategy performance
- [ ] Decide on next steps (optimization vs new strategy)

### Technical Details

#### Class Structure

**ORBStrategy** (`orb_strategy.py`):
- `identify_opening_range()`: Calculate OR levels for each day
- `add_technical_indicators()`: Add ATR, volume metrics, RSI
- `generate_signals()`: Create long/short entry signals
- `calculate_stops_targets()`: Determine stop and target levels
- `calculate_position_size()`: Kelly-based sizing with adjustments
- `_validate_entry()`: Additional entry filters (volume, ATR, etc.)

**ORBBacktest** (`orb_backtest.py`):
- `run_backtest()`: Execute full backtest on historical data
- `calculate_performance()`: Compute all performance metrics
- `generate_report()`: Create markdown performance report
- `_enter_trade()`: Handle new position entries
- `_check_exits()`: Monitor and execute exits (stops, targets, time)
- `_update_equity()`: Track equity curve

**Trade** (`orb_backtest.py`):
- Represents individual trade with entry/exit details
- Handles partial exits (scaled profit taking)
- Calculates P&L and R-multiple

### Logging

The strategy includes comprehensive logging:

```python
# Enable/disable verbose logging in config
VERBOSE_LOGGING = True
LOG_FILE = 'orb_strategy.log'
```

Logs include:
- Strategy initialization
- Opening range calculations
- Signal generation
- Trade entries and exits
- Position sizing decisions
- Exit reasons (stop loss, target, time)

### Testing

Run the configuration validator:
```bash
python3 orb_config.py
```

Run the strategy test:
```bash
python3 orb_strategy.py
```

### Dependencies

- pandas
- numpy
- logging (standard library)
- datetime (standard library)

### Performance Optimization

The implementation includes several optimizations:
- Vectorized calculations where possible
- Efficient DataFrame operations
- Minimal data copying
- Pre-calculated indicators reused across signals

### Support

For issues or questions:
1. Check the logs in `orb_strategy.log`
2. Verify configuration with `python3 orb_config.py`
3. Review the plan in `../../docs/ORB_STRATEGY_PLAN.md`

---

**Status**: Day 1 Complete ✅

**Next**: Day 2 - Data Preparation & Testing
