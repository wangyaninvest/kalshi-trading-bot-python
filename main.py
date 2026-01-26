"""
Kalshi Trading Bot - Market Scanner
Scans Kalshi prediction markets based on configurable criteria.
"""
import os
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
from clients import KalshiHttpClient, Environment
from scanner import MarketScanner, print_market_results
import config

# Load environment variables from .env file
load_dotenv()

# Determine environment (DEMO or PROD) and load appropriate credentials
env = Environment.DEMO if config.ENVIRONMENT == "DEMO" else Environment.PROD
KEYID = os.getenv('DEMO_KEYID') if env == Environment.DEMO else os.getenv('PROD_KEYID')
KEYFILE = os.getenv('DEMO_KEYFILE') if env == Environment.DEMO else os.getenv('PROD_KEYFILE')

# Load and parse private key for API authentication
try:
    with open(KEYFILE, "rb") as key_file:
        private_key = serialization.load_pem_private_key(key_file.read(), password=None)
except FileNotFoundError:
    raise FileNotFoundError(f"Private key file not found at {KEYFILE}")
except Exception as e:
    raise Exception(f"Error loading private key: {str(e)}")

# Initialize Kalshi API client
client = KalshiHttpClient(key_id=KEYID, private_key=private_key, environment=env)

# Display header and account information
print("=" * 50)
print("KALSHI TRADING BOT - MARKET SCANNER")
print("=" * 50)
print(f"Environment: {config.ENVIRONMENT}")
balance = client.get_balance()
print(f"Account Balance: ${balance.get('balance', 0) / 100:.2f}\n")

# Initialize market scanner with top series from CSV
scanner = MarketScanner(client)

# Display scanning configuration
print(f"Configuration:")
print(f"  - Days until close: {config.DAYS_UNTIL_CLOSE}")
print(f"  - Days after start: {config.DAYS_AFTER_START}")
print(f"  - Probability range: {config.MIN_PROBABILITY:.0%} - {config.MAX_PROBABILITY:.0%}")
print(f"  - Require liquidity: {config.REQUIRE_LIQUIDITY}")
print()

# Scan markets with configured criteria
matching_markets = scanner.scan_markets(
    days_until_close=config.DAYS_UNTIL_CLOSE,
    days_after_start=config.DAYS_AFTER_START,
    min_probability=config.MIN_PROBABILITY,
    max_probability=config.MAX_PROBABILITY,
    require_liquidity=config.REQUIRE_LIQUIDITY
)

# Display results
print_market_results(matching_markets)