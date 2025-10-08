"""
Download Extended Intraday Data - Day 3 Extension
Uses Alpha Vantage API to fetch 6-12 months of 5-minute data
Uses TIME_SERIES_INTRADAY_EXTENDED for longer historical periods
"""

import requests
import pandas as pd
import time
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY2')  # Use the second API key
BASE_URL = "https://www.alphavantage.co/query"
OUTPUT_DIR = "/Users/quangnguyen/Desktop/Algo Trading/data/intraday/5min"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)


class ExtendedIntradayCollector:
    """
    Collects extended intraday data from Alpha Vantage
    Can fetch up to 2 years of 5-minute data in monthly slices
    """

    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = BASE_URL
        self.call_count = 0
        self.last_call_time = None

        if not self.api_key or self.api_key == 'YOUR_API_KEY_HERE':
            print("ERROR: Please set ALPHA_VANTAGE_API_KEY2 in .env file")
            sys.exit(1)

    def rate_limit_wait(self):
        """Wait to respect API rate limits (5 calls per minute for free tier)"""
        if self.last_call_time:
            elapsed = time.time() - self.last_call_time
            min_interval = 12  # 12 seconds between calls = 5 calls/min
            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                print(f"  ⏳ Rate limiting: waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)

    def fetch_month_slice(self, symbol, year, month):
        """
        Fetch one month of 5-minute data

        Args:
            symbol: Stock ticker (e.g., 'SPY')
            year: Year (e.g., '2024')
            month: Month (e.g., '1', '2', ..., '12')

        Returns:
            DataFrame with OHLCV data for that month
        """
        self.rate_limit_wait()

        # Format year-month slice parameter
        slice_param = f"year{year}month{month}"

        params = {
            'function': 'TIME_SERIES_INTRADAY_EXTENDED',
            'symbol': symbol,
            'interval': '5min',
            'slice': slice_param,
            'apikey': self.api_key
        }

        try:
            print(f"  📥 Fetching {symbol} {year}-{month:02d}...")
            response = requests.get(self.base_url, params=params)
            self.last_call_time = time.time()
            self.call_count += 1

            if response.status_code != 200:
                print(f"  ❌ HTTP Error {response.status_code}")
                return None

            # Check if response is CSV (success) or JSON (error)
            if 'application/json' in response.headers.get('Content-Type', ''):
                error_data = response.json()
                if "Error Message" in error_data:
                    print(f"  ❌ API Error: {error_data['Error Message']}")
                    return None
                if "Note" in error_data:
                    print(f"  ⚠️  API Limit: {error_data['Note']}")
                    return None

            # Parse CSV response
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))

            # Convert time column to datetime
            df['time'] = pd.to_datetime(df['time'])
            df = df.set_index('time')
            df = df.sort_index()

            # Rename columns to match our format
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

            print(f"  ✅ Retrieved {len(df)} bars for {symbol} {year}-{month:02d}")
            return df

        except Exception as e:
            print(f"  ❌ Error fetching {symbol} {year}-{month}: {str(e)}")
            return None

    def fetch_extended_period(self, symbol, num_months=6):
        """
        Fetch multiple months of data and combine

        Args:
            symbol: Stock ticker
            num_months: Number of months to fetch (default 6)

        Returns:
            Combined DataFrame with all data
        """
        print(f"\n{'='*70}")
        print(f"Downloading {num_months} months of 5-minute data for {symbol}")
        print(f"{'='*70}")

        all_data = []
        current_date = datetime.now()

        # Calculate which months to download
        year = current_date.year
        month = current_date.month

        months_to_fetch = []
        for i in range(num_months):
            months_to_fetch.append((year, month))
            month -= 1
            if month == 0:
                month = 12
                year -= 1

        # Reverse to get chronological order
        months_to_fetch.reverse()

        # Fetch each month
        for year, month in months_to_fetch:
            df = self.fetch_month_slice(symbol, year, month)
            if df is not None and not df.empty:
                all_data.append(df)
            else:
                print(f"  ⚠️  Skipping {year}-{month:02d} (no data)")

        if not all_data:
            print(f"\n❌ No data retrieved for {symbol}")
            return None

        # Combine all months
        combined_df = pd.concat(all_data)
        combined_df = combined_df.sort_index()

        # Remove duplicates (overlapping data points)
        combined_df = combined_df[~combined_df.index.duplicated(keep='first')]

        # Filter to market hours only (9:30 AM - 4:00 PM ET)
        combined_df = self.filter_market_hours(combined_df)

        print(f"\n{'='*70}")
        print(f"✅ Downloaded {len(combined_df)} total bars for {symbol}")
        print(f"📅 Date range: {combined_df.index.min()} to {combined_df.index.max()}")
        print(f"📊 Trading days: {len(combined_df.index.date.unique())}")
        print(f"{'='*70}")

        return combined_df

    @staticmethod
    def filter_market_hours(df):
        """Filter to only include regular market hours (9:30 AM - 4:00 PM ET)"""
        # Keep only data between 9:30 AM and 4:00 PM
        df = df.between_time('09:30', '16:00')
        return df

    def save_data(self, df, symbol):
        """Save data to CSV"""
        output_path = os.path.join(OUTPUT_DIR, f"{symbol}_extended.csv")
        df.to_csv(output_path)
        print(f"💾 Saved to: {output_path}")
        return output_path


def main():
    """Main execution"""
    print("\n" + "="*70)
    print("EXTENDED INTRADAY DATA DOWNLOADER")
    print("Using Alpha Vantage TIME_SERIES_INTRADAY_EXTENDED")
    print("="*70)

    # Initialize collector
    collector = ExtendedIntradayCollector(API_KEY)

    # Symbols to download
    symbols = ['SPY']  # Start with SPY only

    # Number of months to download
    print("\nHow many months of historical data do you want?")
    print("1. 6 months (recommended for Day 3)")
    print("2. 12 months (ideal for robust testing)")
    print("3. 24 months (maximum available)")

    choice = input("\nEnter choice (1/2/3): ").strip()

    months_map = {'1': 6, '2': 12, '3': 24}
    num_months = months_map.get(choice, 6)

    print(f"\n📊 Will download {num_months} months of data")
    print(f"⚠️  This will use approximately {num_months} API calls per symbol")
    print(f"⚠️  Free tier limit: 25 calls/day, 5 calls/minute")

    # Download data
    results = {}
    for symbol in symbols:
        df = collector.fetch_extended_period(symbol, num_months)
        if df is not None:
            output_path = collector.save_data(df, symbol)
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
    print(f"API calls made: {collector.call_count}")
    print(f"Symbols downloaded: {len(results)}")

    for symbol, info in results.items():
        print(f"\n{symbol}:")
        print(f"  Bars: {info['bars']:,}")
        print(f"  Range: {info['date_range'][0]} to {info['date_range'][1]}")
        print(f"  File: {info['path']}")

    print("\n✅ Download complete!")
    print("\nNext step: Run optimization on extended data")
    print("  python strategies/orb/parameter_optimization.py")
    print("="*70)


if __name__ == "__main__":
    main()
