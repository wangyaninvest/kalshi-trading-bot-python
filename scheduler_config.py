"""
Configuration for the Kalshi trading bot scheduler.
"""

# Timezone for scheduling (uses tzdata format)
# Examples: "America/New_York" (EST/EDT), "America/Chicago" (CST/CDT), 
#           "America/Los_Angeles" (PST/PDT), "UTC"
TIMEZONE = "America/New_York"

# Starting hour for the first run of the day (0-23, in 24-hour format)
# Example: 0 = midnight, 9 = 9 AM, 18 = 6 PM
STARTING_HOUR = 0

# Interval between runs in hours
# Example: 6 = run every 6 hours, 4 = run every 4 hours
INTERVAL_HOURS = 2

# Examples of common schedules:
# - Every 6 hours from midnight: STARTING_HOUR=0, INTERVAL_HOURS=6 → 00:00, 06:00, 12:00, 18:00
# - Every 4 hours from 8 AM: STARTING_HOUR=8, INTERVAL_HOURS=4 → 08:00, 12:00, 16:00, 20:00
# - Every 8 hours from midnight: STARTING_HOUR=0, INTERVAL_HOURS=8 → 00:00, 08:00, 16:00
# - Every 12 hours from 9 AM: STARTING_HOUR=9, INTERVAL_HOURS=12 → 09:00, 21:00
# - Once daily at 9 AM: STARTING_HOUR=9, INTERVAL_HOURS=24 → 09:00
