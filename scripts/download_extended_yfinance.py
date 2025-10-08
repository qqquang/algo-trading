"""
Download Extended Intraday Data using yfinance
Much simpler and can get 60 days of 5-minute data for free
No API key required!
"""

import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

# Configuration
OUTPUT_DIR = "/Users/quangnguyen/Desktop/Algo Trading/data/intraday/5min"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def download_intraday_data(symbol, period='60d', interval='5m'):
    """
    Download intraday data using yfinance

    Args:
        symbol: Stock ticker (e.g., 'SPY')
        period: Time period ('7d', '60d', '1mo', '3mo', '6mo', '1y', '2y')
                Note: For 5-min data, max is 60 days
        interval: Time interval ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h')

    Returns:
        DataFrame with OHLCV data
    """
    print(f"\n{'='*70}")
    print(f"Downloading {period} of {interval} data for {symbol}")
    print(f"Using yfinance (free, no API key required)")
    print(f"{'='*70}\n")

    try:
        # Download data
        print(f"📥 Fetching data...")
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            print(f"❌ No data retrieved for {symbol}")
            return None

        # Clean up data
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]

        # Filter to market hours only (9:30 AM - 4:00 PM ET)
        print(f"📊 Filtering to market hours (9:30 AM - 4:00 PM ET)...")
        df = df.between_time('09:30', '16:00')

        # Remove any timezone info for consistency
        df.index = df.index.tz_localize(None)

        print(f"\n✅ Downloaded {len(df)} bars for {symbol}")
        print(f"📅 Date range: {df.index.min()} to {df.index.max()}")

        # Calculate summary stats
        trading_days = len(pd.Series(df.index.date).unique())
        avg_bars_per_day = len(df) / trading_days if trading_days > 0 else 0

        print(f"📊 Trading days: {trading_days}")
        print(f"📈 Avg bars per day: {avg_bars_per_day:.1f} (expected: 78 for 5-min)")

        return df

    except Exception as e:
        print(f"❌ Error downloading {symbol}: {str(e)}")
        return None


def save_data(df, symbol, suffix='extended'):
    """Save data to CSV"""
    if df is None or df.empty:
        return None

    output_path = os.path.join(OUTPUT_DIR, f"{symbol}_{suffix}.csv")
    df.to_csv(output_path)
    print(f"\n💾 Saved to: {output_path}")
    return output_path


def validate_data(df):
    """Quick validation of downloaded data"""
    if df is None or df.empty:
        return False

    print(f"\n{'='*70}")
    print(f"DATA VALIDATION")
    print(f"{'='*70}")

    # Check for missing data
    missing = df.isnull().sum()
    if missing.any():
        print(f"⚠️  Missing values detected:")
        print(missing[missing > 0])
    else:
        print(f"✅ No missing values")

    # Check for duplicates
    duplicates = df.index.duplicated().sum()
    if duplicates > 0:
        print(f"⚠️  {duplicates} duplicate timestamps found")
    else:
        print(f"✅ No duplicate timestamps")

    # Check value ranges
    if (df['Low'] > df['High']).any():
        print(f"❌ ERROR: Low > High detected!")
        return False

    if (df['Close'] > df['High']).any() or (df['Close'] < df['Low']).any():
        print(f"❌ ERROR: Close outside High/Low range!")
        return False

    print(f"✅ Price ranges valid")

    # Check for reasonable values
    if df['Volume'].min() < 0:
        print(f"❌ ERROR: Negative volume!")
        return False

    print(f"✅ Volume values valid")

    print(f"\n✅ Data validation passed!")
    return True


def main():
    """Main execution"""
    print("\n" + "="*70)
    print("EXTENDED INTRADAY DATA DOWNLOADER")
    print("Using yfinance (free, unlimited)")
    print("="*70)

    # Symbols to download
    symbols = ['SPY', 'QQQ', 'TSLA']

    print("\nAvailable options:")
    print("1. Download 60 days (maximum for 5-min data)")
    print("2. Download 30 days")
    print("3. Download 7 days (testing)")

    choice = input("\nEnter choice (1/2/3): ").strip()

    period_map = {
        '1': '60d',
        '2': '30d',
        '3': '7d'
    }

    period = period_map.get(choice, '60d')

    print(f"\n📊 Downloading {period} of 5-minute data")
    print(f"📋 Symbols: {', '.join(symbols)}")

    results = {}

    for symbol in symbols:
        # Download data
        df = download_intraday_data(symbol, period=period, interval='5m')

        if df is not None:
            # Validate
            if validate_data(df):
                # Save
                output_path = save_data(df, symbol)
                results[symbol] = {
                    'data': df,
                    'path': output_path,
                    'bars': len(df),
                    'date_range': (df.index.min(), df.index.max())
                }

    # Summary
    print("\n" + "="*70)
    print("DOWNLOAD SUMMARY")
    print("="*70)
    print(f"Symbols downloaded: {len(results)}/{len(symbols)}")

    for symbol, info in results.items():
        print(f"\n{symbol}:")
        print(f"  Bars: {info['bars']:,}")
        print(f"  Range: {info['date_range'][0]} to {info['date_range'][1]}")
        print(f"  File: {info['path']}")

    if results:
        print("\n✅ Download complete!")
        print("\nNext steps:")
        print("1. Update parameter_optimization.py to use new data files")
        print("2. Run optimization: python strategies/orb/parameter_optimization.py")
        print("3. Review results and adjust strategy")
    else:
        print("\n❌ No data downloaded!")

    print("="*70)


if __name__ == "__main__":
    main()
