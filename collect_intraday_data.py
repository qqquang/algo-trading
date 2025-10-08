"""
Alpha Vantage Intraday Data Collection Script
Collects 15-minute data for high-liquidity symbols
Includes rate limiting to respect API limits
"""

import requests
import pandas as pd
import numpy as np
import time
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import sys

# Import configuration
try:
    from config import (
        ALPHA_VANTAGE_API_KEY,
        ALPHA_VANTAGE_CALLS_PER_MINUTE,
        INTRADAY_SYMBOLS,
        INTRADAY_INTERVAL,
        OUTPUT_SIZE,
        INTRADAY_DATA_DIR
    )
except ImportError:
    print("Error: config.py not found or missing configuration")
    print("Please ensure config.py exists with your Alpha Vantage API key")
    sys.exit(1)


class AlphaVantageCollector:
    """
    Collects intraday data from Alpha Vantage with rate limiting
    """

    def __init__(self):
        self.api_key = ALPHA_VANTAGE_API_KEY
        self.base_url = "https://www.alphavantage.co/query"
        self.call_count = 0
        self.last_call_time = None
        self.daily_calls = 0
        self.session = requests.Session()

        # Check API key
        if self.api_key == 'YOUR_API_KEY_HERE':
            print("Error: Please set your Alpha Vantage API key in config.py or .env file")
            sys.exit(1)

        # Create data directory if it doesn't exist
        os.makedirs(INTRADAY_DATA_DIR, exist_ok=True)

    def rate_limit_wait(self):
        """
        Implement rate limiting to respect API limits
        5 calls per minute for free tier
        """
        if self.last_call_time:
            elapsed = time.time() - self.last_call_time
            min_interval = 60 / ALPHA_VANTAGE_CALLS_PER_MINUTE  # 12 seconds for 5 calls/min
            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                print(f"  Rate limiting: waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)

    def fetch_intraday_data(self, symbol: str, interval: str = '15min') -> Optional[pd.DataFrame]:
        """
        Fetch intraday data for a single symbol

        Args:
            symbol: Stock symbol
            interval: Time interval (1min, 5min, 15min, 30min, 60min)

        Returns:
            DataFrame with intraday data or None if error
        """
        # Rate limiting
        self.rate_limit_wait()

        # API parameters
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': interval,
            'outputsize': OUTPUT_SIZE,  # 'full' for maximum data
            'apikey': self.api_key,
            'datatype': 'json'
        }

        try:
            print(f"  Fetching {interval} data for {symbol}...")
            response = self.session.get(self.base_url, params=params)
            self.last_call_time = time.time()
            self.call_count += 1
            self.daily_calls += 1

            if response.status_code != 200:
                print(f"  Error: HTTP {response.status_code}")
                return None

            data = response.json()

            # Check for API errors
            if "Error Message" in data:
                print(f"  Error: {data['Error Message']}")
                return None

            if "Note" in data:
                print(f"  API Limit Warning: {data['Note']}")
                return None

            # Extract time series data
            time_series_key = f'Time Series ({interval})'
            if time_series_key not in data:
                print(f"  Error: No time series data found")
                return None

            # Convert to DataFrame
            df = pd.DataFrame.from_dict(data[time_series_key], orient='index')

            # Rename columns
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

            # Convert to numeric
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                df[col] = pd.to_numeric(df[col])

            # Convert index to datetime
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()

            # Add useful columns
            df['Symbol'] = symbol
            df['Returns'] = df['Close'].pct_change()

            # Calculate technical indicators
            df = self.add_technical_indicators(df)

            print(f"  ✓ Retrieved {len(df)} data points for {symbol}")
            return df

        except requests.exceptions.RequestException as e:
            print(f"  Network error: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            print(f"  JSON parsing error: {str(e)}")
            return None
        except Exception as e:
            print(f"  Unexpected error: {str(e)}")
            return None

    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators useful for intraday trading

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with indicators added
        """
        # VWAP (Volume Weighted Average Price)
        df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()

        # RSI for intraday (using 14 periods)
        df['RSI_14'] = self.calculate_rsi(df['Close'], 14)

        # Moving averages (periods adjusted for intraday)
        df['SMA_20'] = df['Close'].rolling(20).mean()
        df['SMA_50'] = df['Close'].rolling(50).mean()
        df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()

        # Bollinger Bands
        bb_period = 20
        df['BB_Middle'] = df['Close'].rolling(bb_period).mean()
        bb_std = df['Close'].rolling(bb_period).std()
        df['BB_Upper'] = df['BB_Middle'] + (2 * bb_std)
        df['BB_Lower'] = df['BB_Middle'] - (2 * bb_std)

        # ATR (Average True Range)
        df['ATR'] = self.calculate_atr(df)

        # Volume metrics
        df['Volume_SMA'] = df['Volume'].rolling(20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']

        return df

    @staticmethod
    def calculate_rsi(prices, period=14):
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def calculate_atr(df, period=14):
        """Calculate Average True Range"""
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(period).mean()
        return atr

    def save_data(self, df: pd.DataFrame, symbol: str) -> bool:
        """
        Save data to CSV and Parquet formats

        Args:
            df: DataFrame to save
            symbol: Stock symbol

        Returns:
            True if successful, False otherwise
        """
        try:
            # File paths
            csv_path = os.path.join(INTRADAY_DATA_DIR, f"{symbol}.csv")
            parquet_path = os.path.join(INTRADAY_DATA_DIR, f"{symbol}.parquet")

            # Save as CSV
            df.to_csv(csv_path)

            # Save as Parquet (more efficient for large datasets)
            df.to_parquet(parquet_path)

            print(f"  ✓ Data saved to {csv_path}")
            return True

        except Exception as e:
            print(f"  Error saving data: {str(e)}")
            return False

    def collect_all_symbols(self, symbols: List[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Collect intraday data for all specified symbols

        Args:
            symbols: List of symbols to collect (uses config default if None)

        Returns:
            Dictionary of DataFrames keyed by symbol
        """
        if symbols is None:
            symbols = INTRADAY_SYMBOLS

        results = {}
        metadata = {
            'collection_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'interval': INTRADAY_INTERVAL,
            'symbols_collected': [],
            'symbols_failed': [],
            'total_data_points': 0
        }

        print("\n" + "="*60)
        print(f"Alpha Vantage Intraday Data Collection")
        print(f"Interval: {INTRADAY_INTERVAL}")
        print(f"Symbols: {', '.join(symbols)}")
        print("="*60)

        for i, symbol in enumerate(symbols, 1):
            print(f"\n[{i}/{len(symbols)}] Processing {symbol}...")

            # Check daily limit
            if self.daily_calls >= ALPHA_VANTAGE_CALLS_PER_DAY:
                print("⚠️  Daily API limit reached. Please continue tomorrow.")
                break

            # Fetch data
            df = self.fetch_intraday_data(symbol, INTRADAY_INTERVAL)

            if df is not None and not df.empty:
                # Save data
                if self.save_data(df, symbol):
                    results[symbol] = df
                    metadata['symbols_collected'].append(symbol)
                    metadata['total_data_points'] += len(df)
            else:
                metadata['symbols_failed'].append(symbol)
                print(f"  ✗ Failed to collect data for {symbol}")

        # Save metadata
        self.save_metadata(metadata)

        # Print summary
        print("\n" + "="*60)
        print("Collection Summary")
        print("="*60)
        print(f"Symbols collected: {len(metadata['symbols_collected'])}/{len(symbols)}")
        print(f"Total data points: {metadata['total_data_points']:,}")
        print(f"API calls made: {self.call_count}")

        if metadata['symbols_failed']:
            print(f"Failed symbols: {', '.join(metadata['symbols_failed'])}")

        print(f"Data saved to: {INTRADAY_DATA_DIR}")
        print("="*60)

        return results

    def save_metadata(self, metadata: Dict):
        """Save collection metadata"""
        metadata_path = os.path.join(INTRADAY_DATA_DIR, 'collection_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)


def validate_data(symbol: str) -> bool:
    """
    Validate collected data for a symbol

    Args:
        symbol: Stock symbol

    Returns:
        True if data is valid
    """
    csv_path = os.path.join(INTRADAY_DATA_DIR, f"{symbol}.csv")

    if not os.path.exists(csv_path):
        print(f"No data file found for {symbol}")
        return False

    try:
        df = pd.read_csv(csv_path, index_col=0, parse_dates=True)

        # Check for required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_cols):
            print(f"Missing required columns for {symbol}")
            return False

        # Check for data completeness
        if len(df) < 100:
            print(f"Warning: Only {len(df)} data points for {symbol}")

        # Check for gaps
        time_diffs = df.index.to_series().diff()
        expected_interval = pd.Timedelta(minutes=15) if '15min' in INTRADAY_INTERVAL else pd.Timedelta(minutes=5)

        # During market hours, intervals should be consistent
        large_gaps = time_diffs[time_diffs > expected_interval * 2]
        if len(large_gaps) > 0:
            print(f"Note: {len(large_gaps)} gaps detected in {symbol} data (expected for overnight/weekend gaps)")

        return True

    except Exception as e:
        print(f"Error validating {symbol}: {str(e)}")
        return False


def main():
    """Main execution function"""
    # Initialize collector
    collector = AlphaVantageCollector()

    # Option to test with single symbol first
    print("\nTest with single symbol first? (recommended)")
    print("1. Yes - Test with SPY only")
    print("2. No - Collect all symbols")

    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == '1':
        # Test with single symbol
        print("\nTesting with SPY...")
        df = collector.fetch_intraday_data('SPY', INTRADAY_INTERVAL)
        if df is not None:
            collector.save_data(df, 'SPY')
            validate_data('SPY')
            print("\n✓ Test successful! Run again with option 2 to collect all symbols.")
    else:
        # Collect all symbols
        results = collector.collect_all_symbols()

        # Validate all collected data
        print("\nValidating collected data...")
        for symbol in results.keys():
            validate_data(symbol)


if __name__ == "__main__":
    main()