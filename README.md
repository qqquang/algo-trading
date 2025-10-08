# Algorithmic Trading Research & Backtesting Platform

A comprehensive Python-based platform for researching, backtesting, and implementing algorithmic trading strategies with a focus on data-driven approaches and risk management.

## 🎯 Project Overview

This repository implements multiple trading strategies based on academic research and practitioner experience, with proper backtesting infrastructure and risk controls. The primary focus is on strategies with robust historical performance across different market regimes.

## 📊 Implemented Strategies

### 1. RSI(2) Mean Reversion (Currently Implemented)
- **Win Rate**: 59.6%
- **Sharpe Ratio**: 0.89
- **Max Drawdown**: -15.04%
- **Annual Return**: ~11% (backtested over 10 years)

Based on the research showing equity mean reversion as one of the most profitable systematic strategies.

### 2. Coming Soon
- Multi-Asset Time-Series Momentum (TSMOM)
- Opening Range Breakout (ORB)
- Bollinger Band Mean Reversion
- Options Premium Harvesting

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/algo-trading.git
cd algo-trading
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Collect historical data:
```bash
python collect_daily_data.py
```

4. Run backtest:
```bash
python rsi2_strategy_fixed.py
```

## 📁 Project Structure

```
algo-trading/
├── data/                          # Historical market data
│   └── daily/
│       ├── stocks/               # Individual stock data
│       ├── etfs/                 # ETF data
│       ├── indicators/           # Market indicators (VIX, etc.)
│       └── metadata/             # Data collection metadata
├── collect_daily_data.py         # Data collection script
├── rsi2_strategy_fixed.py        # RSI(2) mean reversion strategy
├── backtest_rsi2_mean_reversion.py  # Alternative backtest implementation
├── requirements.txt              # Python dependencies
├── CLAUDE.md                     # AI assistant guidelines
├── trading_strategy_research_report.md  # Comprehensive strategy research
├── historical_data_requirements.md      # Data specifications
└── README.md                     # This file
```

## 📈 Data Collection

The platform uses free data from Yahoo Finance by default, with support for:
- **47 liquid symbols** including SPY, QQQ, major stocks, and sector ETFs
- **10 years of daily OHLCV data**
- **Technical indicators** (RSI, Bollinger Bands, Moving Averages, ATR)
- **Automatic data updates** and validation

### Running Data Collection
```bash
python collect_daily_data.py
```

This will download:
- Index ETFs (SPY, QQQ, IWM, DIA)
- Top tech stocks (AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA)
- Large-cap stocks across sectors
- Sector ETFs (XLF, XLK, XLE, etc.)
- Market indicators (VIX, TLT, GLD)

## 🔬 Backtesting Framework

The backtesting system includes:
- **Realistic execution** modeling with slippage considerations
- **Position sizing** using volatility-based methods
- **Risk management** with stop-losses and time-based exits
- **Portfolio-level** constraints and diversification
- **Performance metrics** (Sharpe, Sortino, Max DD, Win Rate)

### Running a Backtest
```bash
# Single strategy backtest
python rsi2_strategy_fixed.py

# Results are saved to:
# - rsi2_trades.csv (all trades)
# - rsi2_strategy_results.png (equity curve)
```

## 📊 Performance Metrics

The framework calculates comprehensive metrics including:
- Total Return
- Sharpe Ratio
- Maximum Drawdown
- Win Rate
- Average Win/Loss
- Profit Factor
- Average Holding Period

## 🛠️ Development

### Adding New Strategies

1. Create a new strategy file in the project root
2. Inherit from base strategy class (to be implemented)
3. Define entry/exit signals
4. Implement position sizing logic
5. Add to backtest suite

### Data Extensions

To add new data sources:
1. Modify `collect_daily_data.py` to include new symbols
2. Update `historical_data_requirements.md` with specifications
3. Run data collection script

## 📚 Documentation

- **[Trading Strategy Research Report](trading_strategy_research_report.md)**: Comprehensive analysis of multiple trading strategies
- **[Historical Data Requirements](historical_data_requirements.md)**: Detailed data specifications for each strategy
- **[CLAUDE.md](CLAUDE.md)**: Guidelines for AI-assisted development

## ⚠️ Risk Disclaimer

**IMPORTANT**: This software is for educational and research purposes only.

- Past performance does not guarantee future results
- Trading involves substantial risk of loss
- Not investment advice
- Always validate strategies with out-of-sample data
- Consider transaction costs, slippage, and market impact

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Research based on academic papers from SSRN, AQR, and Alpha Architect
- Inspired by work from Andreas Clenow, Larry Connors, and other practitioners
- Built with open-source tools: pandas, numpy, yfinance, matplotlib

## 📧 Contact

For questions or suggestions, please open an issue on GitHub.

---

**Note**: Always paper trade strategies before risking real capital. Ensure you understand the risks involved in algorithmic trading.