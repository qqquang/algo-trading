# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an algorithmic trading project. As the codebase is currently being initialized, future development should focus on building a robust trading system with proper risk management, backtesting capabilities, and live trading functionality.

## Common Development Tasks

Since this is a new project, the following setup tasks will likely be needed:

### Python Project Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies (once requirements.txt exists)
pip install -r requirements.txt

# Run tests (once test framework is set up)
pytest tests/
```

### Jupyter Notebook Development
```bash
# Start Jupyter notebook server
jupyter notebook

# Or use JupyterLab
jupyter lab
```

## Architecture Considerations

When building this algorithmic trading system, consider implementing:

1. **Data Pipeline**: Module for fetching, cleaning, and storing market data
2. **Strategy Engine**: Framework for implementing and backtesting trading strategies
3. **Risk Management**: Position sizing, stop-loss, and portfolio management utilities
4. **Execution System**: Order management and broker API integration
5. **Monitoring**: Logging, performance tracking, and alerting systems

## Key Dependencies to Consider

For algorithmic trading in Python, these libraries are commonly used:
- `pandas` and `numpy` for data manipulation
- `yfinance` or `alpaca-py` for market data
- `backtrader` or `zipline` for backtesting
- `ta` or `talib` for technical indicators
- `plotly` or `matplotlib` for visualization

## Development Guidelines

1. Always validate market data before using it in strategies
2. Implement proper error handling for API calls and network issues
3. Use configuration files for API keys and trading parameters (never commit credentials)
4. Include comprehensive logging for debugging trading decisions
5. Write unit tests for strategy logic and risk management rules
6. Document strategy assumptions and backtesting parameters