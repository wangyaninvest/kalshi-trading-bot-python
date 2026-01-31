"""
Scheduler to run the Kalshi trading bot at specific times daily.
"""
import time
import subprocess
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import scheduler_config


# Load configuration
TIMEZONE = ZoneInfo(scheduler_config.TIMEZONE)
STARTING_HOUR = scheduler_config.STARTING_HOUR
INTERVAL_HOURS = scheduler_config.INTERVAL_HOURS


def generate_run_times(starting_hour: int, interval_hours: int) -> list[str]:
    """Generate run times based on starting hour and interval."""
    run_times = []
    hour = starting_hour
    while hour < 24:
        run_times.append(f"{hour:02d}:00")
        hour += interval_hours
    return run_times


# Generate scheduled run times based on configuration
RUN_TIMES = generate_run_times(STARTING_HOUR, INTERVAL_HOURS)


def run_trading_bot():
    """Execute the trading bot."""
    print(f"\n{'='*80}")
    print(f"Starting trading bot run at {datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"{'='*80}\n")
    
    try:
        # First, fetch top series
        print("Step 1: Fetching top series...")
        result = subprocess.run(
            ["python3", "fetch_top_series.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=False,
            text=True
        )
        
        if result.returncode != 0:
            print(f"\n✗ fetch_top_series.py exited with code {result.returncode}")
            print("Aborting trading bot run.\n")
            return
        
        print(f"\n✓ Top series fetch completed successfully")
        
        # Verify the output file exists and has content
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "top_series.csv")
        if not os.path.exists(csv_path):
            print(f"\n✗ Error: Expected output file not found: {csv_path}")
            print("Aborting trading bot run.\n")
            return
        
        if os.path.getsize(csv_path) == 0:
            print(f"\n✗ Error: Output file is empty: {csv_path}")
            print("Aborting trading bot run.\n")
            return
        
        print(f"✓ Verified output file: {csv_path}\n")
        
        # Then run the bot
        print("Step 2: Running trading bot...")
        result = subprocess.run(
            ["python3", "run_bot.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print(f"\n✓ Trading bot completed successfully")
        else:
            print(f"\n✗ Trading bot exited with code {result.returncode}")
            
    except Exception as e:
        print(f"\n✗ Error running trading bot: {e}")
    
    print(f"\n{'='*80}")
    print(f"Trading bot run finished at {datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"{'='*80}\n")


def get_next_run_time():
    """Calculate the next scheduled run time."""
    now = datetime.now(TIMEZONE)
    current_time = now.strftime("%H:%M")
    
    # Find the next run time today
    for run_time in RUN_TIMES:
        if run_time > current_time:
            # Parse the run time
            hour, minute = map(int, run_time.split(":"))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return next_run
    
    # If no more runs today, schedule first run tomorrow
    hour, minute = map(int, RUN_TIMES[0].split(":"))
    next_run = (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    return next_run


def main():
    """Main scheduler loop."""
    print("Kalshi Trading Bot Scheduler")
    print(f"Timezone: {TIMEZONE}")
    print(f"Configuration: Starting hour={STARTING_HOUR}, Interval={INTERVAL_HOURS}h")
    print(f"Scheduled run times: {', '.join(RUN_TIMES)}")
    print(f"Started at: {datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
    
    while True:
        next_run = get_next_run_time()
        now = datetime.now(TIMEZONE)
        wait_seconds = (next_run - now).total_seconds()
        
        print(f"Next run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"Waiting {wait_seconds/3600:.2f} hours...\n")
        
        # Sleep until next run time
        time.sleep(wait_seconds)
        
        # Run the bot
        run_trading_bot()
        
        # Small delay to avoid running multiple times in the same minute
        time.sleep(60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScheduler stopped by user.")
    except Exception as e:
        print(f"\n\nScheduler error: {e}")
