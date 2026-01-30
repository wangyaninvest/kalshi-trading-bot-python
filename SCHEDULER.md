# Trading Bot Scheduler

## Configuration

Edit the configuration in `scheduler_config.py`:

```python
# Timezone for scheduling
TIMEZONE = "America/New_York"  # EST/EDT

# Starting hour for the first run (0-23, in 24-hour format)
STARTING_HOUR = 0

# Interval between runs in hours
INTERVAL_HOURS = 6
```

**Default configuration**: Runs at 00:00, 06:00, 12:00, and 18:00 EST/EDT (every 6 hours starting at midnight)

**Example configurations:**
- Every 4 hours starting at 8 AM: `STARTING_HOUR = 8`, `INTERVAL_HOURS = 4` → 08:00, 12:00, 16:00, 20:00
- Every 8 hours starting at midnight: `STARTING_HOUR = 0`, `INTERVAL_HOURS = 8` → 00:00, 08:00, 16:00
- Every 12 hours starting at 9 AM: `STARTING_HOUR = 9`, `INTERVAL_HOURS = 12` → 09:00, 21:00
- Once daily at 9 AM: `STARTING_HOUR = 9`, `INTERVAL_HOURS = 24` → 09:00

**Timezone options:**
- `"America/New_York"` - Eastern Time (EST/EDT)
- `"America/Chicago"` - Central Time (CST/CDT)
- `"America/Los_Angeles"` - Pacific Time (PST/PDT)
- `"UTC"` - Coordinated Universal Time

## Running the Scheduler

The trading bot is configured to run automatically based on your configuration.

### Option 1: Run in Terminal (Foreground)

```bash
python scheduler.py
```

The scheduler will display when the next run is scheduled and wait until that time.

### Option 2: Run in Background

```bash
./run_scheduler.sh &
```

Or using nohup to keep it running even after logout:

```bash
nohup python scheduler.py > scheduler.log 2>&1 &
```

Check the process:
```bash
ps aux | grep scheduler.py
```

Stop the scheduler:
```bash
pkill -f scheduler.py
```

### Option 3: Run as a macOS Service (Persistent)

Create a launchd service that starts automatically:

1. Create the plist file:
```bash
nano ~/Library/LaunchAgents/com.kalshi.tradingbot.plist
```

2. Add this content (replace `/path/to/your/` with actual path):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.kalshi.tradingbot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/yanwang/Work/kalshi-trading-bot-python/scheduler.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/yanwang/Work/kalshi-trading-bot-python</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/yanwang/Work/kalshi-trading-bot-python/scheduler.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/yanwang/Work/kalshi-trading-bot-python/scheduler.error.log</string>
</dict>
</plist>
```

3. Load the service:
```bash
launchctl load ~/Library/LaunchAgents/com.kalshi.tradingbot.plist
```

4. Check status:
```bash
launchctl list | grep kalshi
```

5. Stop the service:
```bash
launchctl unload ~/Library/LaunchAgents/com.kalshi.tradingbot.plist
```

## Monitoring

View logs in real-time:
```bash
tail -f scheduler.log
```

Check if scheduler is running:
```bash
ps aux | grep scheduler
```

## Notes

- The scheduler uses Eastern Time (EST/EDT) and automatically handles daylight saving time
- Each run is logged with timestamps
- The scheduler will continue running until manually stopped
- If a run is missed (e.g., computer was off), it will run at the next scheduled time
