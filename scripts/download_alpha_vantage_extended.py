"""
Download Extended Historical Data using Alpha Vantage API
Focus on 1-2 symbols to maximize data depth within API limits
Uses TIME_SERIES_INTRADAY with outputsize=full
"""

import requests
import pandas as pd
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY2')
BASE_URL = "https://www.alphavantage.co/query"
OUTPUT_DIR = "/Users/quangnguyen/Desktop/Algo Trading/data/intraday/5min"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# API limits
CALLS_PER_MINUTE = 5
DAILY_LIMIT = 25  # Free tier limit


class AlphaVantageExtendedDownloader:
    """Download extended intraday data from Alpha Vantage"""

    def __init__(self, api_key):
        self.api_key = api_key
        self.call_count = 0
        self.last_call_time = None

        if not self.api_key:
            print("❌ ERROR: ALPHA_VANTAGE_API_KEY2 not found in .env")
            exit(1)

    def rate_limit_wait(self):
        """Wait to respect 5 calls/minute rate limit"""
        if self.last_call_time:
            elapsed = time.time() - self.last_call_time
            min_interval = 60 / CALLS_PER_MINUTE  # 12 seconds
            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                print(f"  ⏳ Rate limit wait: {wait_time:.1f}s...")
                time.sleep(wait_time)

    def fetch_intraday_full(self, symbol, interval='5min'):
        """
        Fetch FULL intraday data for a symbol

        Alpha Vantage returns:
        - outputsize=compact: Latest 100 data points
        - outputsize=full: Full history (up to 2 years for 1min, varies by interval)

        For 5min interval, typically get 1-3 months of data
        """
        self.rate_limit_wait()

        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': interval,
            'outputsize': 'full',  # Get maximum available data
            'apikey': self.api_key,
            'datatype': 'json'
        }

        try:
            print(f"\n{'='*70}")
            print(f"📥 Fetching FULL {interval} data for {symbol}")
            print(f"   Using Alpha Vantage API (outputsize=full)")
            print(f"{'='*70}")

            response = requests.get(BASE_URL, params=params)
            self.last_call_time = time.time()
            self.call_count += 1

            if response.status_code != 200:
                print(f"❌ HTTP Error {response.status_code}")
                return None

            data = response.json()

            # Check for errors
            if "Error Message" in data:
                print(f"❌ API Error: {data['Error Message']}")
                return None

            if "Note" in data:
                print(f"⚠️  API Limit: {data['Note']}")
                print(f"   You've hit the rate limit. Wait or try tomorrow.")
                return None

            if "Information" in data:
                print(f"⚠️  Info: {data['Information']}")
                return None

            # Get the time series key
            time_series_key = f'Time Series ({interval})'
            if time_series_key not in data:
                print(f"❌ No time series data found in response")
                print(f"   Keys in response: {list(data.keys())}")
                return None

            # Parse data
            time_series = data[time_series_key]

            # Convert to DataFrame
            df = pd.DataFrame.from_dict(time_series, orient='index')

            # Rename columns
            column_map = {
                '1. open': 'Open',
                '2. high': 'High',
                '3. low': 'Low',
                '4. close': 'Close',
                '5. volume': 'Volume'
            }
            df = df.rename(columns=column_map)

            # Convert to numeric
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                df[col] = pd.to_numeric(df[col])

            # Convert index to datetime
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()

            # Filter to market hours (9:30 AM - 4:00 PM ET)
            df = df.between_time('09:30', '16:00')

            # Remove timezone info
            df.index = df.index.tz_localize(None)

            print(f"\n✅ Downloaded {len(df)} bars")
            print(f"📅 Date range: {df.index.min()} to {df.index.max()}")

            # Calculate stats
            trading_days = len(pd.Series(df.index.date).unique())
            months = (df.index.max() - df.index.min()).days / 30.0

            print(f"📊 Trading days: {trading_days}")
            print(f"📆 Time span: {months:.1f} months")
            print(f"📈 Avg bars/day: {len(df)/trading_days:.1f}")

            return df

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None

    def save_data(self, df, symbol, suffix='alpha_vantage'):
        """Save data to CSV"""
        if df is None or df.empty:
            return None

        output_path = os.path.join(OUTPUT_DIR, f"{symbol}_{suffix}.csv")
        df.to_csv(output_path)
        print(f"\n💾 Saved to: {output_path}")
        return output_path


def main():
    """Main execution"""
    print("\n" + "="*70)
    print("ALPHA VANTAGE EXTENDED DATA DOWNLOADER")
    print("="*70)
    print(f"API Key: {os.getenv('ALPHA_VANTAGE_API_KEY2')[:8]}...")
    print(f"Rate Limit: {CALLS_PER_MINUTE} calls/minute, {DAILY_LIMIT} calls/day")

    downloader = AlphaVantageExtendedDownloader(API_KEY)

    # Focus on 1-2 symbols to maximize data depth
    print("\nWhich symbol(s) to download?")
    print("1. SPY only (recommended - saves API calls)")
    print("2. SPY + QQQ (uses 2 calls)")
    print("3. SPY + TSLA (uses 2 calls)")

    choice = input("\nEnter choice (1/2/3): ").strip()

    symbol_map = {
        '1': ['SPY'],
        '2': ['SPY', 'QQQ'],
        '3': ['SPY', 'TSLA']
    }

    symbols = symbol_map.get(choice, ['SPY'])

    print(f"\n📋 Will download: {', '.join(symbols)}")
    print(f"⚠️  This will use {len(symbols)} API call(s)")
    print(f"⚠️  You have {DAILY_LIMIT} calls/day limit on free tier")

    input("\nPress Enter to continue...")

    results = {}

    for symbol in symbols:
        # Download data
        df = downloader.fetch_intraday_full(symbol, interval='5min')

        if df is not None:
            # Save
            output_path = downloader.save_data(df, symbol)
            results[symbol] = {
                'data': df,
                'path': output_path,
                'bars': len(df),
                'date_range': (df.index.min(), df.index.max()),
                'days': len(pd.Series(df.index.date).unique())
            }

    # Summary
    print("\n" + "="*70)
    print("DOWNLOAD SUMMARY")
    print("="*70)
    print(f"API calls used: {downloader.call_count}/{DAILY_LIMIT}")
    print(f"Symbols downloaded: {len(results)}/{len(symbols)}")

    for symbol, info in results.items():
        months = (info['date_range'][1] - info['date_range'][0]).days / 30.0
        print(f"\n{symbol}:")
        print(f"  Bars: {info['bars']:,}")
        print(f"  Trading days: {info['days']}")
        print(f"  Time span: {months:.1f} months")
        print(f"  Range: {info['date_range'][0]} to {info['date_range'][1]}")
        print(f"  File: {info['path']}")

    if results:
        print("\n✅ Download complete!")
        print("\nNext steps:")
        print("1. Update parameter_optimization.py to use new files")
        print("2. Run optimization on extended data")
        print("3. Compare results with yfinance data (60 days)")
    else:
        print("\n❌ No data downloaded")
        print("   Check API key or rate limits")

    print("="*70)


if __name__ == "__main__":
    main()
