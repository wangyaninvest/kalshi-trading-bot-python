"""
Configuration file for Kalshi trading bot.
Adjust these settings to customize the market scanning behavior.
"""

# ============================================================================
# API Configuration
# ============================================================================
# Toggle between DEMO and PROD environments
# Options: "DEMO" or "PROD"
ENVIRONMENT = "PROD"

# ============================================================================
# Market Scanning Criteria
# ============================================================================
# Maximum days until market closes
# Markets closing within this timeframe will be included
DAYS_UNTIL_CLOSE = 7

# Minimum days since market opened
# Markets must be open for at least this many days to be included
# This filters out newly created markets
DAYS_AFTER_START = 14

# Minimum probability threshold (0.0 to 1.0)
# Markets with YES or NO probability >= this value will be included
# Example: 0.90 means 90% probability
MIN_PROBABILITY = 0.6

# Maximum probability threshold (0.0 to 1.0)
# Markets with YES or NO probability <= this value will be included
# Example: 0.99 means 99% probability
# Use with MIN_PROBABILITY to create a probability range
MAX_PROBABILITY = 0.95

# Whether to require liquidity (open orders) in the orderbook
# Setting to False will speed up scanning as it skips orderbook checks
REQUIRE_LIQUIDITY = False

# Probability of skipping a matching market (0.0 to 1.0)
# Use this to throttle trading frequency
# Example: 0.5 means 50% chance to skip each matching market
# Set to 0.0 to never skip (trade all matching markets)
THROTTLE_PROBABILITY = 0.0

# Amount to spend per trade in dollars
# Each matching market will trigger a buy order for this amount
TRADE_AMOUNT = 1.0

# Maximum number of contracts to hold per market
# Prevents over-concentration from repeated buys on the same market
# Set to 0 to disable this check
MAX_POSITION_SIZE = 15

# Dry run mode - scan markets without placing trades
# Set to True to only find and print matching markets
# Set to False to actually place orders
DRY_RUN = False
