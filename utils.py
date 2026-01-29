"""
Utility functions for the Kalshi trading bot.
"""
from datetime import datetime
from typing import Dict, Tuple, Any


def parse_iso_timestamp(timestamp_str: str) -> datetime:
    """
    Parse ISO timestamp, handling microseconds > 6 digits and timezone notation.
    
    Args:
        timestamp_str: ISO format timestamp string
        
    Returns:
        Parsed datetime object
    """
    if not timestamp_str:
        return datetime.now()
        
    timestamp_str = timestamp_str.replace('Z', '+00:00')
    
    if '.' in timestamp_str and '+' in timestamp_str:
        parts = timestamp_str.split('.')
        microseconds_and_tz = parts[1].split('+')
        # Python datetime only supports up to 6 digits for microseconds
        if len(microseconds_and_tz[0]) > 6:
            microseconds_and_tz[0] = microseconds_and_tz[0][:6]
        timestamp_str = f"{parts[0]}.{microseconds_and_tz[0]}+{microseconds_and_tz[1]}"
    
    try:
        return datetime.fromisoformat(timestamp_str)
    except ValueError:
        return datetime.now()


def calculate_mid_probabilities(market: Dict[str, Any]) -> Tuple[float, float]:
    """
    Calculate mid-market probabilities for YES and NO sides based on bid/ask.
    
    Args:
        market: Market data from API
        
    Returns:
        Tuple of (yes_probability, no_probability)
    """
    yes_bid = float(market.get('yes_bid_dollars', 0))
    yes_ask = float(market.get('yes_ask_dollars', 0))
    no_bid = float(market.get('no_bid_dollars', 0))
    no_ask = float(market.get('no_ask_dollars', 0))
    
    yes_prob = (yes_bid + yes_ask) / 2 if (yes_bid > 0 and yes_ask > 0) else 0
    no_prob = (no_bid + no_ask) / 2 if (no_bid > 0 and no_ask > 0) else 0
    
    return yes_prob, no_prob
