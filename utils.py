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
