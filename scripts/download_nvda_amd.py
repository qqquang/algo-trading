"""
Quick script to download NVDA and AMD extended data for Day 5 testing
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def download_extended_5min(symbol, days=60):
    """Download extended 5-minute data"""
    print(f"\nDownloading {symbol} - {days} days of 5-min data...")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date, interval='5m')

    if df.empty:
        print(f"  ❌ No data retrieved for {symbol}")
        return None

    print(f"  ✓ Retrieved {len(df)} bars")
    print(f"  Date range: {df.index.min()} to {df.index.max()}")

    # Save as CSV
    output_path = f"/Users/quangnguyen/Desktop/Algo Trading/data/intraday/5min/{symbol}_extended.csv"
    df.to_csv(output_path)
    print(f"  💾 Saved to: {output_path}")

    return df

if __name__ == "__main__":
    print("="*80)
    print("DOWNLOADING NVDA AND AMD - 60 DAY EXTENDED DATA")
    print("="*80)

    # Download NVDA
    nvda_df = download_extended_5min('NVDA', days=60)

    # Download AMD
    amd_df = download_extended_5min('AMD', days=60)

    print("\n" + "="*80)
    print("DOWNLOAD COMPLETE")
    print("="*80)
