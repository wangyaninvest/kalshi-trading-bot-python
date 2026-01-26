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
DAYS_UNTIL_CLOSE = 30

# Minimum days since market opened
# Markets must be open for at least this many days to be included
# This filters out newly created markets
DAYS_AFTER_START = 10

# Minimum probability threshold (0.0 to 1.0)
# Markets with YES or NO probability >= this value will be included
# Example: 0.90 means 90% probability
MIN_PROBABILITY = 0.6

# Maximum probability threshold (0.0 to 1.0)
# Markets with YES or NO probability <= this value will be included
# Example: 0.99 means 99% probability
# Use with MIN_PROBABILITY to create a probability range
MAX_PROBABILITY = 0.9

# Whether to require liquidity (open orders) in the orderbook
# Setting to False will speed up scanning as it skips orderbook checks
REQUIRE_LIQUIDITY = False
