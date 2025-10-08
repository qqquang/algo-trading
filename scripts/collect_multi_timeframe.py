"""
Multi-Timeframe Intraday Data Collection - Plan A
Collects 5min, 1min, 30min data for core symbols
Plus 15min for additional volatile symbols
"""

from collect_intraday_data import AlphaVantageCollector
import time

def main():
    """Execute Plan A data collection"""

    collector = AlphaVantageCollector()

    print("="*70)
    print("PLAN A: Multi-Timeframe Intraday Data Collection")
    print("="*70)
    print("\nCollection Plan:")
    print("  Phase 1: 5-min data (SPY, QQQ, AAPL, MSFT, NVDA) - 5 calls")
    print("  Phase 2: 1-min data (SPY, QQQ, TSLA, NVDA, AAPL) - 5 calls")
    print("  Phase 3: 30-min data (SPY, QQQ, AAPL, MSFT, NVDA) - 5 calls")
    print("  Phase 4: 15-min data (TSLA, META, GOOGL, AMZN, JPM) - 5 calls")
    print("\nTotal: 20 API calls")
    print("="*70)

    proceed = input("\nProceed with collection? (y/n): ").strip().lower()
    if proceed != 'y':
        print("Collection cancelled.")
        return

    # Phase 1: 5-minute data for core symbols
    print("\n" + "="*70)
    print("PHASE 1: Collecting 5-minute data")
    print("="*70)
    symbols_5min = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA']

    for i, symbol in enumerate(symbols_5min, 1):
        print(f"\n[{i}/5] Processing {symbol} (5min)...")
        if collector.daily_calls >= 25:
            print("⚠️  Daily API limit reached!")
            break

        df = collector.fetch_intraday_data(symbol, '5min')
        if df is not None:
            # Save to 5min directory
            import os
            os.makedirs('./data/intraday/5min', exist_ok=True)
            csv_path = f'./data/intraday/5min/{symbol}.csv'
            parquet_path = f'./data/intraday/5min/{symbol}.parquet'
            df.to_csv(csv_path)
            df.to_parquet(parquet_path)
            print(f"  ✓ Saved {len(df)} bars to {csv_path}")

    # Phase 2: 1-minute data for high-volume symbols
    print("\n" + "="*70)
    print("PHASE 2: Collecting 1-minute data")
    print("="*70)
    symbols_1min = ['SPY', 'QQQ', 'TSLA', 'NVDA', 'AAPL']

    for i, symbol in enumerate(symbols_1min, 1):
        print(f"\n[{i}/5] Processing {symbol} (1min)...")
        if collector.daily_calls >= 25:
            print("⚠️  Daily API limit reached!")
            break

        df = collector.fetch_intraday_data(symbol, '1min')
        if df is not None:
            import os
            os.makedirs('./data/intraday/1min', exist_ok=True)
            csv_path = f'./data/intraday/1min/{symbol}.csv'
            parquet_path = f'./data/intraday/1min/{symbol}.parquet'
            df.to_csv(csv_path)
            df.to_parquet(parquet_path)
            print(f"  ✓ Saved {len(df)} bars to {csv_path}")

    # Phase 3: 30-minute data for core symbols
    print("\n" + "="*70)
    print("PHASE 3: Collecting 30-minute data")
    print("="*70)
    symbols_30min = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA']

    for i, symbol in enumerate(symbols_30min, 1):
        print(f"\n[{i}/5] Processing {symbol} (30min)...")
        if collector.daily_calls >= 25:
            print("⚠️  Daily API limit reached!")
            break

        df = collector.fetch_intraday_data(symbol, '30min')
        if df is not None:
            import os
            os.makedirs('./data/intraday/30min', exist_ok=True)
            csv_path = f'./data/intraday/30min/{symbol}.csv'
            parquet_path = f'./data/intraday/30min/{symbol}.parquet'
            df.to_csv(csv_path)
            df.to_parquet(parquet_path)
            print(f"  ✓ Saved {len(df)} bars to {csv_path}")

    # Phase 4: 15-minute data for additional volatile symbols
    print("\n" + "="*70)
    print("PHASE 4: Collecting 15-minute data (additional symbols)")
    print("="*70)
    symbols_15min_extra = ['TSLA', 'META', 'GOOGL', 'AMZN', 'JPM']

    for i, symbol in enumerate(symbols_15min_extra, 1):
        print(f"\n[{i}/5] Processing {symbol} (15min)...")
        if collector.daily_calls >= 25:
            print("⚠️  Daily API limit reached!")
            break

        df = collector.fetch_intraday_data(symbol, '15min')
        if df is not None:
            import os
            os.makedirs('./data/intraday/15min', exist_ok=True)
            csv_path = f'./data/intraday/15min/{symbol}.csv'
            parquet_path = f'./data/intraday/15min/{symbol}.parquet'
            df.to_csv(csv_path)
            df.to_parquet(parquet_path)
            print(f"  ✓ Saved {len(df)} bars to {csv_path}")

    # Final Summary
    print("\n" + "="*70)
    print("COLLECTION COMPLETE!")
    print("="*70)
    print(f"\nTotal API calls used: {collector.daily_calls}")
    print(f"Remaining calls today: {25 - collector.daily_calls}")

    print("\n📊 Data Collected:")
    print("  5-min:  SPY, QQQ, AAPL, MSFT, NVDA")
    print("  1-min:  SPY, QQQ, TSLA, NVDA, AAPL")
    print("  30-min: SPY, QQQ, AAPL, MSFT, NVDA")
    print("  15-min: SPY, QQQ, AAPL, MSFT, NVDA (previous)")
    print("          + TSLA, META, GOOGL, AMZN, JPM (new)")

    print("\n✅ Ready for multi-timeframe strategy development!")

if __name__ == "__main__":
    main()