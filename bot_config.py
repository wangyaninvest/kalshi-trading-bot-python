"""Configuration for Kalshi trading bot."""

# API
ENVIRONMENT = "PROD"  # "DEMO" or "PROD"

# Market scanning criteria
DAYS_UNTIL_CLOSE = 4
DAYS_AFTER_START = 8
MIN_PROBABILITY = 0.7
MAX_PROBABILITY = 0.95
REQUIRE_LIQUIDITY = True
THROTTLE_PROBABILITY = 0.3  # chance to skip each matching market
TRADE_AMOUNT = 1.0  # dollars per trade
MAX_POSITION_SIZE = 10  # max contracts per market
DRY_RUN = False
