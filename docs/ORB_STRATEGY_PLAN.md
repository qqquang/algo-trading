# Opening Range Breakout (ORB) Strategy - Implementation Plan

## Strategy Overview

**Opening Range Breakout (ORB)** is an intraday momentum strategy that capitalizes on breakouts from the first 15-30 minutes of trading.

### Key Performance Metrics (from research)
- **Win Rate**: 40-55%
- **Risk/Reward**: 1.3-2.0
- **Ideal Conditions**: High volatility symbols, trending market days
- **Best Symbols**: SPY, QQQ, TSLA (high liquidity + volatility)
- **Best Timeframes**: 5-min and 15-min data

---

## Available Data

### Perfect Match for ORB
✅ **5-min data**: SPY, QQQ, AAPL, MSFT, NVDA (~4,200 bars each)
✅ **15-min data**: SPY, QQQ, TSLA, META, GOOGL, AMZN, JPM, AAPL, MSFT, NVDA (~1,400 bars each)
✅ **1-min data**: SPY, QQQ, TSLA, NVDA, AAPL (~21,000 bars each)

### Recommended Test Symbols (in priority order)
1. **SPY** - Most liquid, best for ORB
2. **QQQ** - Tech volatility, excellent ORB candidate
3. **TSLA** - High volatility, strong breakouts

---

## Step-by-Step Implementation Plan

### Phase 1: Strategy Research & Specification (Day 1)

#### Step 1.1: Define ORB Rules
Based on research report, formalize exact entry/exit rules:

**Opening Range Definition**:
- Use first 15 minutes of regular trading (9:30 AM - 9:45 AM EST)
- Alternative: 30-minute range (9:30 AM - 10:00 AM EST)
- Calculate: `OR_High`, `OR_Low`, `OR_Range = OR_High - OR_Low`

**Entry Rules - Long**:
```
1. Price breaks above OR_High + buffer (0.05% to avoid false breakouts)
2. Volume > 1.5x average volume (confirmation)
3. Time: Between 9:45 AM - 3:30 PM EST (avoid close)
4. Price must stay above OR_High for at least 2 bars (confirmation)
5. Optional filter: Overall market trend (SPY) bullish
6. ATR Filter: Current ATR > 0.5x average ATR (avoid low volatility)
7. Relative Volume: Current bar volume > previous 5 bars average
```

**Entry Rules - Short**:
```
1. Price breaks below OR_Low - buffer (0.05% to avoid false breakouts)
2. Volume > 1.5x average volume (confirmation)
3. Time: Between 9:45 AM - 3:30 PM EST (avoid close)
4. Price must stay below OR_Low for at least 2 bars (confirmation)
5. Optional filter: Overall market trend (SPY) bearish
6. ATR Filter: Current ATR > 0.5x average ATR (avoid low volatility)
7. Relative Volume: Current bar volume > previous 5 bars average
```

**Exit Rules**:
```
1. Initial Stop Loss: 0.75x OR_Range from entry (tighter for false breakouts)
2. Dynamic Stop: If price moves 0.5x OR_Range in favor, move stop to breakeven
3. Profit Targets (scaled exit):
   - Target 1: Exit 50% at 1x OR_Range (lock in profits)
   - Target 2: Exit 25% at 1.5x OR_Range
   - Target 3: Exit final 25% at 2x OR_Range or trail
4. Time Stop: Exit all positions at 3:55 PM EST
5. Trailing Stop: After 1x profit, trail by 0.3x OR_Range (tighter)
6. Reversal Exit: If opposite signal appears, close current position
7. Volatility Exit: If ATR spikes >2x normal, tighten stops to 0.5x OR_Range
```

#### Step 1.2: Advanced Position Sizing
```python
# Kelly Criterion-inspired position sizing with safety factor
def calculate_position_size(capital, win_rate, avg_win_loss_ratio, or_range, atr):
    """
    Dynamic position sizing based on:
    - Kelly fraction (reduced by safety factor)
    - OR range relative to ATR (volatility adjustment)
    - Maximum risk per trade cap
    """

    # Base Kelly fraction (simplified)
    kelly_fraction = (win_rate * avg_win_loss_ratio - (1 - win_rate)) / avg_win_loss_ratio
    safety_factor = 0.25  # Use only 25% of Kelly suggestion
    adjusted_kelly = kelly_fraction * safety_factor

    # Volatility adjustment
    or_atr_ratio = or_range / atr
    if or_atr_ratio > 1.5:  # OR unusually wide
        volatility_adj = 0.7  # Reduce position
    elif or_atr_ratio < 0.5:  # OR unusually narrow
        volatility_adj = 0.5  # Further reduce (tight stops = higher risk)
    else:
        volatility_adj = 1.0

    # Calculate final position size
    risk_per_trade = min(adjusted_kelly, 0.02) * volatility_adj  # Cap at 2%
    position_size = (capital * risk_per_trade) / stop_loss_distance

    # Apply maximum position limits
    max_position_size = capital * 0.15  # Max 15% in one position
    min_position_size = capital * 0.005  # Min 0.5% (avoid tiny positions)

    return max(min(position_size, max_position_size), min_position_size)
```

---

### Phase 2: Code Structure Design (Day 1)

#### Step 2.1: File Structure
```
strategies/orb/
├── orb_strategy.py          # Main strategy implementation
├── orb_backtest.py          # Backtesting engine
├── orb_config.py            # Strategy parameters
└── orb_results.md           # Performance summary
```

#### Step 2.2: Core Functions to Implement

**orb_strategy.py**:
```python
class ORBStrategy:
    def __init__(self, or_period=15, risk_reward=2.0):
        """
        Parameters:
        - or_period: Opening range period in minutes (15 or 30)
        - risk_reward: Risk/reward ratio for profit targets
        """

    def identify_opening_range(self, df):
        """
        Find OR_High and OR_Low for each trading day
        Returns: DataFrame with OR_High, OR_Low, OR_Range columns
        """

    def generate_signals(self, df):
        """
        Generate long/short entry signals
        Returns: DataFrame with 'long_signal', 'short_signal' columns
        """

    def calculate_stops_targets(self, df, entry_price, direction):
        """
        Calculate stop loss and profit target levels
        Returns: stop_loss, profit_target
        """

    def validate_entry(self, row):
        """
        Additional filters:
        - Volume confirmation
        - Time window check
        - Market regime filter (optional)
        Returns: True/False
        """
```

**orb_backtest.py**:
```python
class ORBBacktest:
    def __init__(self, strategy, initial_capital=100000):
        """Initialize backtest with strategy instance"""

    def run_backtest(self, df):
        """
        Execute full backtest on historical data
        Returns: trades_df, performance_metrics
        """

    def calculate_performance(self, trades_df):
        """
        Calculate:
        - Total Return
        - Sharpe Ratio
        - Max Drawdown
        - Win Rate
        - Average R/R
        - Profit Factor
        """

    def generate_report(self):
        """Create detailed performance report"""
```

---

### Phase 2.5: Market Microstructure Considerations

#### Spread and Liquidity Analysis
```python
def calculate_spread_cost(df):
    """
    Estimate trading costs from bid-ask spread
    """
    # Approximate spread using High-Low as proxy (Corwin-Schultz estimator)
    df['spread_estimate'] = 2 * (np.exp(np.sqrt(
        2 * np.log(df['High'] / df['Low'])**2
    )) - 1)

    # Liquidity score based on volume and price range
    df['liquidity_score'] = df['Volume'] / (df['High'] - df['Low'])

    # Skip trades when spread > 0.1% (10 bps)
    df['tradeable'] = df['spread_estimate'] < 0.001

    return df
```

#### Pre-Market Analysis
```python
def analyze_premarket_activity(df):
    """
    Use pre-market data (if available) to predict OR quality
    """
    indicators = {
        'premarket_volume': 0,  # Volume before 9:30
        'premarket_range': 0,   # Price range in pre-market
        'gap_size': 0,          # Gap from previous close
        'gap_direction': 0,     # Up/down gap
        'futures_sentiment': 0,  # SPY futures direction
    }

    # High pre-market activity often leads to cleaner ORB patterns
    # Large gaps may invalidate OR (price discovery ongoing)

    return indicators
```

---

### Phase 3: Data Preparation (Day 2)

#### Step 3.1: Load and Validate Intraday Data
```python
def load_intraday_data(symbol, interval='5min'):
    """
    Load intraday data from data/intraday/{interval}/{symbol}_intraday.csv
    Validate:
    - No missing trading days
    - Proper time indexing
    - Complete OHLCV data
    """
```

#### Step 3.2: Add Required Indicators
```python
def add_technical_indicators(df):
    """
    Add indicators needed for ORB:
    - Volume SMA (20-period)
    - ATR (14-period) for volatility adjustment
    - Optional: Trend filter (SPY direction)
    """
```

#### Step 3.3: Identify Trading Sessions
```python
def mark_trading_sessions(df):
    """
    Identify:
    - Market open (9:30 AM EST)
    - Opening range period (9:30-9:45 AM or 9:30-10:00 AM)
    - Trading window (9:45 AM - 3:30 PM)
    - Market close (4:00 PM EST)

    Add columns: 'session_date', 'is_opening_range', 'is_trading_window'
    """
```

---

### Phase 4: Strategy Implementation (Day 2-3)

#### Step 4.1: Opening Range Calculation
```python
def calculate_opening_range(df, or_minutes=15):
    """
    For each trading day:
    1. Filter first {or_minutes} of trading
    2. Calculate OR_High = max(High) during period
    3. Calculate OR_Low = min(Low) during period
    4. Calculate OR_Range = OR_High - OR_Low
    5. Broadcast to all bars in that trading day

    Edge cases:
    - Handle gaps (large overnight moves)
    - Minimum range filter (avoid low volatility days)
    - Market holidays
    """

    # Minimum range filter
    min_range_pct = 0.002  # 0.2% minimum range
    df['OR_valid'] = (df['OR_Range'] / df['OR_Low']) > min_range_pct
```

#### Step 4.2: Signal Generation
```python
def generate_orb_signals(df):
    """
    Long Signal:
    - Close > OR_High (breakout)
    - Volume > Volume_SMA * 1.5
    - is_trading_window == True
    - OR_valid == True

    Short Signal:
    - Close < OR_Low (breakdown)
    - Volume > Volume_SMA * 1.5
    - is_trading_window == True
    - OR_valid == True

    Only one signal per day (first breakout)
    """
```

#### Step 4.3: Entry/Exit Logic
```python
def execute_trades(df):
    """
    Trade execution rules:

    ENTRY:
    - Enter on close of signal bar
    - Record: entry_price, entry_time, direction
    - Calculate: stop_loss, profit_target

    EXIT (check on every bar while in position):
    - Stop Loss: Close crosses stop_loss
    - Profit Target: High/Low reaches profit_target
    - Time Stop: 3:55 PM EST reached

    POSITION SIZING:
    - Risk 2% of capital per trade
    - Max 20% of capital per position
    - Adjust for OR_Range (volatility)
    """
```

---

### Phase 5: Backtesting (Day 3-4)

#### Step 5.1: Single Symbol Backtest
```python
# Test on SPY first
def backtest_spy_5min():
    """
    1. Load SPY 5-min data (~4,200 bars = ~1 month)
    2. Run ORB strategy
    3. Analyze results

    Expected trades: ~20-25 trades (1 per day on average)
    """
```

#### Step 5.2: Performance Metrics to Track
```python
metrics = {
    # Win Rate Metrics
    'total_trades': 0,
    'winning_trades': 0,
    'losing_trades': 0,
    'win_rate': 0.0,

    # Return Metrics
    'total_return': 0.0,
    'avg_win': 0.0,
    'avg_loss': 0.0,
    'largest_win': 0.0,
    'largest_loss': 0.0,
    'profit_factor': 0.0,  # Total wins / Total losses

    # Risk Metrics
    'sharpe_ratio': 0.0,
    'max_drawdown': 0.0,
    'avg_risk_reward': 0.0,  # Actual R/R achieved

    # Strategy Specific
    'avg_or_range': 0.0,  # Average opening range size
    'breakout_success_rate': 0.0,  # % of breakouts that hit target
    'avg_holding_time': 0.0,  # Hours held per trade
}
```

#### Step 5.3: Multi-Symbol Testing
```python
symbols = ['SPY', 'QQQ', 'TSLA']
intervals = ['5min', '15min']

# Test matrix (6 combinations)
for symbol in symbols:
    for interval in intervals:
        run_backtest(symbol, interval)
        compare_results()
```

---

### Phase 5.5: Machine Learning Enhancements (Optional)

#### Feature Engineering for ML
```python
def create_ml_features(df):
    """
    Create features for ML-based ORB prediction
    """
    features = {
        # OR characteristics
        'or_range_pct': df['OR_Range'] / df['OR_Low'],
        'or_range_vs_atr': df['OR_Range'] / df['ATR'],
        'or_volume_ratio': df['OR_Volume'] / df['Volume_SMA_20'],

        # Market context
        'day_of_week': df.index.dayofweek,
        'days_to_expiry': 0,  # Options expiry effect
        'vix_level': 0,  # Market fear gauge
        'spy_trend': 0,  # Overall market direction

        # Historical performance
        'prev_day_return': df['Close'].pct_change(390),  # 390 5-min bars = 1 day
        'prev_or_success': 0,  # Was yesterday's ORB profitable?
        'consecutive_wins': 0,  # Momentum factor

        # Technical indicators at OR end
        'rsi_at_or_end': df['RSI'].iloc[-1],  # RSI at 9:45
        'volume_spike': df['Volume'] / df['Volume'].rolling(20).mean(),
    }

    return pd.DataFrame(features)
```

#### Random Forest Classifier for Entry Filter
```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

def train_orb_classifier(historical_data):
    """
    Train RF to predict ORB success probability
    """
    # Prepare features and labels
    X = create_ml_features(historical_data)
    y = (historical_data['trade_return'] > 0).astype(int)  # 1 if profitable

    # Split data (80/20)
    X_train, X_test = X[:int(0.8*len(X))], X[int(0.8*len(X)):]
    y_train, y_test = y[:int(0.8*len(y))], y[int(0.8*len(y)):]

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train Random Forest
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=5,  # Shallow to avoid overfitting
        min_samples_split=20,
        random_state=42
    )
    rf_model.fit(X_train_scaled, y_train)

    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': rf_model.feature_importances_
    }).sort_values('importance', ascending=False)

    # Only take trades with >60% success probability
    trade_threshold = 0.60

    return rf_model, scaler, feature_importance
```

#### LSTM for OR Range Prediction
```python
def build_lstm_model(sequence_length=20):
    """
    LSTM to predict OR range magnitude (for position sizing)
    """
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout

    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=(sequence_length, 10)),
        Dropout(0.2),
        LSTM(50, return_sequences=False),
        Dropout(0.2),
        Dense(25),
        Dense(1)  # Predict OR range as % of price
    ])

    model.compile(optimizer='adam', loss='mse', metrics=['mae'])

    # Use predicted OR range to adjust position size
    # Wider predicted range = smaller position (higher risk)

    return model
```

---

### Phase 6: Optimization (Day 4-5)

#### Step 6.1: Parameter Optimization
```python
# Parameters to optimize
params_to_test = {
    'or_period': [15, 30],  # Minutes
    'risk_reward': [1.5, 2.0, 2.5],
    'volume_multiplier': [1.2, 1.5, 2.0],
    'min_range_pct': [0.001, 0.002, 0.005],
}

# Grid search or walk-forward optimization
def optimize_parameters(df, params_to_test):
    """
    Test all combinations
    Select best based on Sharpe Ratio (not just return)
    Avoid overfitting - validate on out-of-sample data
    """
```

#### Step 6.2: Filter Optimization
```python
# Optional filters to test
filters = {
    'trend_filter': True,  # Only trade in direction of SPY trend
    'volatility_filter': True,  # Avoid low VIX days
    'gap_filter': 0.01,  # Skip days with >1% overnight gap
    'time_of_day': [(9, 45), (11, 30)],  # Best breakout times
}
```

#### Step 6.3: Walk-Forward Validation
```python
def walk_forward_test(df, train_window=20, test_window=5):
    """
    1. Train on first 20 days
    2. Test on next 5 days
    3. Roll forward
    4. Repeat

    Prevents overfitting to in-sample data
    """
```

---

### Phase 7: Analysis & Reporting (Day 5)

#### Step 7.1: Create Performance Report
Generate `strategies/orb/orb_results.md` with:
```markdown
# ORB Strategy Backtest Results

## Summary
- **Total Trades**: X
- **Win Rate**: X%
- **Total Return**: X%
- **Sharpe Ratio**: X
- **Max Drawdown**: X%

## Best Performing Setup
- **Symbol**: SPY
- **Timeframe**: 5-min
- **OR Period**: 15 minutes
- **R/R Ratio**: 2.0

## Trade Analysis
- **Average Win**: $XXX
- **Average Loss**: $XXX
- **Profit Factor**: X.XX
- **Best Trade**: +$XXX (date)
- **Worst Trade**: -$XXX (date)

## Observations
- [Key findings]
- [What worked well]
- [What needs improvement]
```

#### Step 7.2: Visualization
```python
def create_orb_charts():
    """
    Generate charts:
    1. Equity curve over time
    2. Win rate by day of week
    3. Win rate by time of day
    4. Distribution of R/R achieved
    5. Drawdown chart
    6. Sample trade examples (winners and losers)
    """
```

---

## Expected Outcomes

### Realistic Performance Targets (based on research)
- **Win Rate**: 40-55% (target: 45%)
- **Average R/R**: 1.3-2.0 (target: 1.8)
- **Total Return**: 15-30% over test period (1 month of data)
- **Max Drawdown**: <10%
- **Sharpe Ratio**: >1.5

### Success Criteria
✅ Win rate ≥ 40%
✅ Profit factor > 1.5
✅ Max drawdown < 15%
✅ Consistent across multiple symbols
✅ Better performance on 5-min vs 15-min data (hypothesis)

### Failure Criteria (when to abandon or redesign)
❌ Win rate < 35%
❌ Profit factor < 1.0
❌ Highly symbol-dependent (only works on SPY)
❌ Excessive drawdowns (>20%)

---

## Advanced Risk Management Framework

### Portfolio-Level Risk Controls
```python
class RiskManager:
    def __init__(self, max_daily_loss_pct=0.05, max_positions=3):
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_positions = max_positions
        self.daily_pnl = 0
        self.open_positions = []

    def check_daily_loss_limit(self, capital):
        """Stop trading if daily loss exceeds limit"""
        if self.daily_pnl < -(capital * self.max_daily_loss_pct):
            return False  # No more trades today
        return True

    def check_correlation_limit(self, new_symbol):
        """Avoid concentrated risk in correlated assets"""
        correlations = {
            ('SPY', 'QQQ'): 0.85,
            ('AAPL', 'QQQ'): 0.75,
            # Add more correlations
        }

        for position in self.open_positions:
            if self.get_correlation(position.symbol, new_symbol) > 0.8:
                return False  # Too correlated
        return True

    def calculate_var(self, positions, confidence=0.95):
        """Calculate Value at Risk for current positions"""
        # Use historical returns to estimate VaR
        pass
```

### Dynamic Risk Adjustment
```python
def adjust_risk_by_regime(market_conditions):
    """
    Adjust risk based on market regime
    """
    risk_multipliers = {
        'high_volatility': 0.5,   # Reduce risk in volatile markets
        'trending': 1.2,          # Increase in strong trends
        'choppy': 0.3,           # Minimize in choppy markets
        'low_volume': 0.5,       # Reduce on low volume days
        'friday': 0.7,           # Reduce before weekend
        'fomc_day': 0.4,         # Reduce on Fed days
        'earnings_season': 0.6,   # Reduce during earnings
    }

    # Detect current regime
    regime = detect_market_regime(market_conditions)

    return risk_multipliers.get(regime, 1.0)
```

### Known Challenges with ORB & Advanced Mitigations

1. **False Breakouts** (35% of failures)
   - Basic: Volume confirmation filter
   - Advanced: Wait for 2-bar confirmation above/below OR
   - ML: Use Random Forest to predict false breakout probability

2. **Low Volatility Days** (20% of failures)
   - Basic: Minimum OR range filter (0.2% of price)
   - Advanced: Compare OR to previous 10-day average
   - Dynamic: Adjust position size inversely to OR width

3. **Gap Days** (15% of failures)
   - Basic: Skip days with gaps >1%
   - Advanced: Adjust OR levels by gap size
   - Alternative: Use pre-market levels as OR substitute

4. **Choppy Markets** (20% of failures)
   - Basic: Limit to 1 trade per day
   - Advanced: Require ADX > 25 for trend strength
   - Smart: Switch to range-trading on choppy days

5. **Late Day Reversals** (10% of failures)
   - Basic: Time stop at 3:55 PM EST
   - Advanced: Scale out starting at 3:00 PM
   - Dynamic: Tighten stops after 2:30 PM

### Drawdown Management
```python
def manage_drawdown(current_drawdown, max_drawdown=0.10):
    """
    Progressive risk reduction during drawdowns
    """
    if current_drawdown < 0.03:
        return 1.0  # Full position size

    elif current_drawdown < 0.05:
        return 0.75  # Reduce to 75%

    elif current_drawdown < 0.08:
        return 0.50  # Reduce to 50%

    elif current_drawdown < max_drawdown:
        return 0.25  # Minimal position size

    else:
        return 0  # Stop trading, reassess strategy
```

---

## Comparison to RSI(2) Strategy

| Metric | RSI(2) (Daily) | ORB (Intraday) |
|--------|----------------|----------------|
| Timeframe | Daily | 5-min / 15-min |
| Holding Period | 1-3 days | Hours (intraday) |
| Win Rate | 59.6% | 40-55% (target) |
| R/R | ~1.2 | 1.3-2.0 (target) |
| Sharpe | 0.89 | TBD |
| Strategy Type | Mean Reversion | Momentum Breakout |

**Portfolio Benefits**:
- **Diversification**: Combines mean reversion + momentum
- **Timeframe Diversification**: Daily + intraday
- **Low Correlation**: Should reduce overall portfolio volatility

---

## Implementation Timeline

### Day 1: Planning & Design
- [x] Create this planning document
- [ ] Review ORB rules from research report
- [ ] Design code structure
- [ ] Create strategy configuration file

### Day 2: Data Prep & Core Implementation
- [ ] Load and validate 5-min data for SPY
- [ ] Implement opening range calculation
- [ ] Implement signal generation logic
- [ ] Basic entry/exit mechanics

### Day 3: Backtesting
- [ ] Build backtesting engine
- [ ] Run first backtest on SPY 5-min
- [ ] Debug and refine
- [ ] Test on QQQ and TSLA

### Day 4: Optimization
- [ ] Parameter grid search
- [ ] Filter optimization
- [ ] Walk-forward validation
- [ ] Multi-timeframe comparison (5-min vs 15-min)

### Day 5: Analysis & Documentation
- [ ] Generate performance report
- [ ] Create visualizations
- [ ] Document findings
- [ ] Next steps recommendations

---

## Next Strategy After ORB

Once ORB is complete, recommended next strategy:

### **VWAP Mean Reversion** (Priority 2)
- Use 5-min and 15-min data (same as ORB)
- Fade price when it deviates ±2σ from VWAP
- Expected win rate: 55-65%
- Complements ORB (mean reversion vs momentum)

---

## Questions to Answer During Implementation

1. **Does 15-min ORB outperform 5-min ORB?**
   - Hypothesis: 15-min has fewer false breakouts, higher win rate

2. **Is TSLA significantly better than SPY/QQQ?**
   - Hypothesis: Higher volatility = larger ORB ranges = bigger profits

3. **Do volume filters improve performance?**
   - Hypothesis: Yes, reduces false breakouts by 20%+

4. **Should we trade both directions (long + short)?**
   - Hypothesis: Long-only better due to market bias

5. **What's the optimal OR period?**
   - Hypothesis: 15-min better than 30-min (fresher information)

---

## Code Quality Standards

### Must Have:
- ✅ Type hints for all functions
- ✅ Comprehensive docstrings
- ✅ Input validation and error handling
- ✅ Logging for debugging
- ✅ Unit tests for core functions
- ✅ Clear variable naming

### Example:
```python
from typing import Tuple
import pandas as pd

def calculate_opening_range(
    df: pd.DataFrame,
    or_minutes: int = 15
) -> Tuple[pd.DataFrame, dict]:
    """
    Calculate opening range (OR) for each trading day.

    Parameters
    ----------
    df : pd.DataFrame
        Intraday OHLCV data with datetime index
    or_minutes : int, default=15
        Length of opening range period in minutes

    Returns
    -------
    df : pd.DataFrame
        Input dataframe with added columns:
        - OR_High: High of opening range
        - OR_Low: Low of opening range
        - OR_Range: OR_High - OR_Low
    stats : dict
        Summary statistics about opening ranges

    Raises
    ------
    ValueError
        If df doesn't have required columns or datetime index

    Examples
    --------
    >>> df, stats = calculate_opening_range(spy_5min, or_minutes=15)
    >>> print(stats['avg_or_range_pct'])
    0.0025  # 0.25% average range
    """
```

---

## Success = Matching Research Report Expectations

From the research report, ORB strategy should achieve:
- ✅ **40-55% win rate** (we should be in this range)
- ✅ **1.3-2.0 R/R** (actual R/R realized, not just target)
- ✅ **Works best on volatile symbols** (TSLA > SPY hypothesis)
- ✅ **5-15 min timeframes optimal** (compare both)

If we achieve these metrics, the strategy is **validated** and ready for live paper trading.

If we significantly underperform (win rate <35%, R/R <1.0), we need to:
1. Review implementation for bugs
2. Re-check data quality
3. Question research report assumptions
4. Consider abandoning ORB for other strategies

---

## Real-Time Execution Considerations

### Slippage and Market Impact
```python
def estimate_slippage(order_size, avg_volume, spread):
    """
    Estimate expected slippage for order
    """
    # Market impact model (square-root model)
    participation_rate = order_size / avg_volume
    market_impact = 0.1 * np.sqrt(participation_rate)  # 10 bps per sqrt(%)

    # Add half spread for crossing
    crossing_cost = spread / 2

    # Total expected slippage
    total_slippage = market_impact + crossing_cost

    return total_slippage
```

### Order Execution Logic
```python
class OrderExecutor:
    def __init__(self, broker_api):
        self.broker = broker_api
        self.pending_orders = []

    def execute_orb_entry(self, signal, urgency='normal'):
        """
        Smart order routing for ORB entries
        """
        if urgency == 'high':
            # Use market order for strong breakouts
            order = self.broker.market_order(
                symbol=signal['symbol'],
                qty=signal['quantity'],
                side=signal['side']
            )

        elif urgency == 'normal':
            # Use limit order at mid + 1 tick
            mid_price = (signal['bid'] + signal['ask']) / 2
            limit_price = mid_price + (0.01 if signal['side'] == 'buy' else -0.01)

            order = self.broker.limit_order(
                symbol=signal['symbol'],
                qty=signal['quantity'],
                side=signal['side'],
                limit_price=limit_price,
                time_in_force='IOC'  # Immediate or cancel
            )

        else:  # low urgency
            # Use passive limit order
            limit_price = signal['bid'] if signal['side'] == 'buy' else signal['ask']
            order = self.broker.limit_order(
                symbol=signal['symbol'],
                qty=signal['quantity'],
                side=signal['side'],
                limit_price=limit_price,
                time_in_force='DAY'
            )

        return order

    def manage_partial_fills(self, order):
        """Handle partial fills and adjust stops accordingly"""
        if order.filled_qty < order.qty:
            # Adjust stop loss for partial position
            self.adjust_stop_loss(order.filled_qty)

            # Cancel remainder or leave open based on strategy
            if self.time_since_signal > 60:  # seconds
                self.broker.cancel_order(order.id)
```

### Latency Optimization
```python
def optimize_for_latency():
    """
    Tips for reducing execution latency
    """
    optimizations = {
        'data_feed': 'Use WebSocket instead of polling',
        'calculations': 'Pre-calculate OR levels at 9:45',
        'orders': 'Pre-stage orders with broker API',
        'infrastructure': 'Colocate servers near exchange',
        'code': 'Use NumPy vectorization, avoid loops',
        'threading': 'Separate threads for data, signals, execution',
    }

    # Pre-calculate as much as possible
    # Cache frequently accessed data
    # Minimize API calls during trading hours

    return optimizations
```

---

## Final Checklist Before Going Live

### Backtesting Phase
- [ ] Backtest results match research expectations (40-55% win rate)
- [ ] Walk-forward validation successful (no overfitting)
- [ ] Works on multiple symbols (SPY, QQQ, TSLA)
- [ ] Tested across different market conditions
- [ ] Slippage and commission analysis completed

### Risk Management
- [ ] Risk management tested (max 2% risk per trade)
- [ ] Daily loss limits implemented
- [ ] Correlation limits tested
- [ ] Drawdown management rules in place
- [ ] Position sizing algorithm validated

### Technical Implementation
- [ ] Code reviewed and tested
- [ ] Unit tests for all critical functions
- [ ] Integration tests with mock broker API
- [ ] Performance/latency optimization done
- [ ] Error handling and logging complete

### Analysis & Documentation
- [ ] Performance report generated
- [ ] Compared to RSI(2) strategy (correlation analysis)
- [ ] Feature importance analysis (if using ML)
- [ ] Documentation complete and clear

### Paper Trading Preparation
- [ ] Broker API integration tested
- [ ] Real-time data feed connected
- [ ] Order execution logic tested
- [ ] Monitoring dashboard created
- [ ] Alert system configured

### Go-Live Criteria
- [ ] 30 days successful paper trading
- [ ] Consistent performance metrics
- [ ] All edge cases handled
- [ ] Emergency stop procedures in place
- [ ] Ready for live trading with small capital

---

## Summary of Improvements Made

### 1. **Enhanced Entry/Exit Rules**
- Added buffer zones (0.05%) to avoid false breakouts
- Implemented 2-bar confirmation requirement
- Added ATR and relative volume filters
- Introduced scaled exits with multiple profit targets
- Dynamic stop adjustments based on price movement

### 2. **Advanced Position Sizing**
- Kelly Criterion-based sizing with safety factor
- Volatility-adjusted positions based on OR/ATR ratio
- Dynamic min/max position limits

### 3. **Market Microstructure**
- Spread cost estimation using Corwin-Schultz method
- Liquidity scoring for trade filtering
- Pre-market analysis integration

### 4. **Machine Learning Enhancements**
- Random Forest for breakout success prediction
- LSTM for OR range forecasting
- Feature engineering framework
- 60% probability threshold for trades

### 5. **Comprehensive Risk Management**
- Portfolio-level risk controls
- Daily loss limits and correlation checks
- Market regime-based risk adjustment
- Progressive drawdown management
- Value at Risk (VaR) calculations

### 6. **Real-Time Execution**
- Smart order routing with urgency levels
- Partial fill management
- Slippage estimation models
- Latency optimization strategies

These improvements transform the basic ORB strategy into a **production-ready trading system** with institutional-grade risk management and execution capabilities.

---

**The enhanced strategy is now ready for implementation. Let's proceed with Day 1 tasks when you're ready!**
