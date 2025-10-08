"""
Configuration file for API keys and settings
IMPORTANT: Add config.py to .gitignore to keep your API keys private
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Alpha Vantage API Configuration
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', 'YOUR_API_KEY_HERE')

# API Rate Limits
ALPHA_VANTAGE_CALLS_PER_MINUTE = 5  # Free tier: 5 calls per minute
ALPHA_VANTAGE_CALLS_PER_DAY = 25    # Free tier: 25 calls per day

# Data Settings
INTRADAY_SYMBOLS = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA']
INTRADAY_INTERVAL = '15min'  # 1min, 5min, 15min, 30min, 60min
OUTPUT_SIZE = 'full'  # 'compact' = last 100 points, 'full' = all available data (up to 2 years)

# Paths
DATA_DIR = './data'
INTRADAY_DATA_DIR = f'{DATA_DIR}/intraday/{INTRADAY_INTERVAL}'