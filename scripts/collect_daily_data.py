"""
Daily Stock Data Collection Script for Equity Mean Reversion Strategy
Priority 1: SPY, QQQ, and top liquid large-cap stocks
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
import warnings
warnings.filterwarnings('ignore')

# Configuration
DATA_DIR = './data/daily'
START_DATE = (datetime.now() - timedelta(days=365*10)).strftime('%Y-%m-%d')  # 10 years
END_DATE = datetime.now().strftime('%Y-%m-%d')

# Priority 1 Symbols - Most liquid stocks for mean reversion
SYMBOLS = {
    # Core Index ETFs (MUST HAVE)
    'index_etfs': ['SPY', 'QQQ', 'IWM', 'DIA'],

    # Mega-cap Tech (Most liquid, best for mean reversion)
    'mega_tech': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA'],

    # Other Liquid Large Caps
    'large_caps': [
        'BRK-B',  # Berkshire
        'JPM',    # Financials leader
        'V',      # Visa
        'MA',     # Mastercard
        'JNJ',    # Healthcare
        'UNH',    # Healthcare
        'XOM',    # Energy
        'WMT',    # Consumer
        'PG',     # Consumer staples
        'HD',     # Retail
        'BAC',    # Bank
        'CVX',    # Energy
        'ABBV',   # Pharma
        'LLY',    # Pharma
        'AVGO',   # Semiconductor
        'ORCL',   # Software
        'COST',   # Retail
        'AMD',    # Semiconductor
        'NFLX',   # Streaming
        'ADBE'    # Software
    ],

    # Sector ETFs for diversification
    'sector_etfs': ['XLF', 'XLK', 'XLE', 'XLV', 'XLI', 'XLP', 'XLU', 'XLB', 'XLY', 'XLRE'],

    # Regime Indicators
    'regime': ['VIX', 'TLT', 'GLD', 'DXY', 'HYG', 'LQD']
}

def create_data_directories():
    """Create directory structure for data storage"""
    directories = [
        DATA_DIR,
        f"{DATA_DIR}/stocks",
        f"{DATA_DIR}/etfs",
        f"{DATA_DIR}/indicators",
        f"{DATA_DIR}/metadata"
    ]

    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
    print("✓ Data directories created")

def download_stock_data(symbol, start_date=START_DATE, end_date=END_DATE):
    """Download historical data for a single symbol"""
    try:
        # Download data with auto-adjust for splits and dividends
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, auto_adjust=True)

        if df.empty:
            print(f"✗ No data found for {symbol}")
            return None

        # Add useful columns
        df['Symbol'] = symbol
        df['Returns'] = df['Close'].pct_change()
        df['Dollar_Volume'] = df['Close'] * df['Volume']

        # Calculate technical indicators for mean reversion
        df['RSI_2'] = calculate_rsi(df['Close'], 2)
        df['RSI_14'] = calculate_rsi(df['Close'], 14)

        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(20).mean()
        df['BB_Std'] = df['Close'].rolling(20).std()
        df['BB_Upper'] = df['BB_Middle'] + (2 * df['BB_Std'])
        df['BB_Lower'] = df['BB_Middle'] - (2 * df['BB_Std'])
        df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])

        # Moving Averages
        df['SMA_50'] = df['Close'].rolling(50).mean()
        df['SMA_200'] = df['Close'].rolling(200).mean()

        # ATR for position sizing
        df['ATR'] = calculate_atr(df)

        return df

    except Exception as e:
        print(f"✗ Error downloading {symbol}: {str(e)}")
        return None

def calculate_rsi(prices, period):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_atr(df, period=14):
    """Calculate Average True Range"""
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.rolling(period).mean()
    return atr

def save_data(df, symbol, category):
    """Save data to appropriate directory"""
    if df is None or df.empty:
        return False

    # Determine subdirectory
    if category in ['index_etfs', 'sector_etfs', 'regime']:
        subdir = 'etfs'
    elif category == 'regime' and symbol == 'VIX':
        subdir = 'indicators'
    else:
        subdir = 'stocks'

    # Save as CSV
    filepath = f"{DATA_DIR}/{subdir}/{symbol}.csv"
    df.to_csv(filepath)

    # Also save as Parquet for faster loading
    filepath_parquet = f"{DATA_DIR}/{subdir}/{symbol}.parquet"
    df.to_parquet(filepath_parquet)

    return True

def collect_all_data():
    """Main function to collect all priority 1 data"""
    create_data_directories()

    all_symbols = []
    metadata = {}

    print("\n" + "="*50)
    print("Starting Priority 1 Data Collection")
    print("="*50)

    for category, symbols in SYMBOLS.items():
        print(f"\n📊 Downloading {category}...")
        print("-" * 30)

        success_count = 0
        for symbol in symbols:
            print(f"  Fetching {symbol}...", end=" ")
            df = download_stock_data(symbol)

            if df is not None and save_data(df, symbol, category):
                print(f"✓ ({len(df)} days)")
                success_count += 1

                # Store metadata
                metadata[symbol] = {
                    'category': category,
                    'start_date': df.index[0].strftime('%Y-%m-%d'),
                    'end_date': df.index[-1].strftime('%Y-%m-%d'),
                    'total_days': len(df),
                    'avg_volume': df['Volume'].mean(),
                    'avg_dollar_volume': df['Dollar_Volume'].mean()
                }
                all_symbols.append(symbol)
            else:
                print("✗ Failed")

        print(f"  Category complete: {success_count}/{len(symbols)} successful")

    # Save metadata
    with open(f"{DATA_DIR}/metadata/collection_info.json", 'w') as f:
        json.dump({
            'collection_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_symbols': len(all_symbols),
            'symbols': all_symbols,
            'metadata': metadata
        }, f, indent=2)

    print("\n" + "="*50)
    print(f"✓ Data Collection Complete!")
    print(f"  Total symbols collected: {len(all_symbols)}")
    print(f"  Data saved to: {os.path.abspath(DATA_DIR)}")
    print("="*50)

    return metadata

def validate_data():
    """Validate downloaded data for completeness and quality"""
    print("\n🔍 Validating Data Quality...")
    print("-" * 30)

    issues = []

    # Check each file
    for subdir in ['stocks', 'etfs', 'indicators']:
        dir_path = f"{DATA_DIR}/{subdir}"
        if not os.path.exists(dir_path):
            continue

        for file in os.listdir(dir_path):
            if file.endswith('.csv'):
                symbol = file.replace('.csv', '')
                df = pd.read_csv(f"{dir_path}/{file}", index_col=0, parse_dates=True)

                # Check for data issues
                if len(df) < 252 * 5:  # Less than 5 years of trading days
                    issues.append(f"{symbol}: Only {len(df)} days of data")

                # Check for gaps
                df['Date_Diff'] = df.index.to_series().diff()
                max_gap = df['Date_Diff'].max()
                if max_gap > pd.Timedelta(days=10):
                    issues.append(f"{symbol}: Large gap detected ({max_gap.days} days)")

                # Check for null values
                null_count = df[['Open', 'High', 'Low', 'Close', 'Volume']].isnull().sum().sum()
                if null_count > 0:
                    issues.append(f"{symbol}: {null_count} null values found")

    if issues:
        print("⚠️  Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✓ All data validated successfully!")

    return issues

def create_summary_report():
    """Create a summary report of collected data"""
    print("\n📈 Generating Summary Report...")
    print("-" * 30)

    # Load metadata
    with open(f"{DATA_DIR}/metadata/collection_info.json", 'r') as f:
        metadata = json.load(f)

    report = []
    report.append("# Data Collection Summary Report")
    report.append(f"\nCollection Date: {metadata['collection_date']}")
    report.append(f"Total Symbols: {metadata['total_symbols']}")

    # Group by category
    by_category = {}
    for symbol, info in metadata['metadata'].items():
        cat = info['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(symbol)

    report.append("\n## Symbols by Category:")
    for cat, symbols in by_category.items():
        report.append(f"\n### {cat} ({len(symbols)} symbols)")
        report.append(", ".join(symbols))

    # High-level statistics
    report.append("\n## Data Statistics:")
    total_days = sum(info['total_days'] for info in metadata['metadata'].values())
    report.append(f"- Total data points: {total_days:,}")
    report.append(f"- Average days per symbol: {total_days/len(metadata['metadata']):,.0f}")

    # Save report
    report_path = f"{DATA_DIR}/metadata/summary_report.md"
    with open(report_path, 'w') as f:
        f.write("\n".join(report))

    print(f"✓ Report saved to: {report_path}")

    # Also print key stats
    print(f"\n📊 Key Statistics:")
    print(f"  - Symbols collected: {metadata['total_symbols']}")
    print(f"  - Total data points: {total_days:,}")
    print(f"  - Ready for backtesting: ✓")

if __name__ == "__main__":
    # Run data collection
    metadata = collect_all_data()

    # Validate data
    issues = validate_data()

    # Generate report
    create_summary_report()

    print("\n🎉 Priority 1 data collection complete!")
    print("Next steps:")
    print("  1. Review the data in ./data/daily/")
    print("  2. Run backtesting on RSI(2) mean reversion strategy")
    print("  3. Test on SPY and QQQ first before expanding")