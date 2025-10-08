"""
Test Alpha Vantage API connection
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if API key is set
api_key = os.getenv('ALPHA_VANTAGE_API_KEY')

if api_key and api_key != 'YOUR_API_KEY_HERE':
    print(f"✓ API key found: {api_key[:4]}...{api_key[-4:]}")
    print("Ready to collect data!")
else:
    print("✗ API key not found in .env file")
    print("\nPlease add to .env file:")
    print("ALPHA_VANTAGE_API_KEY=your_actual_api_key_here")