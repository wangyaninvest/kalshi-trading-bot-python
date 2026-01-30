#!/bin/bash
# Script to run the trading bot scheduler in the background

cd "$(dirname "$0")"

echo "Starting Kalshi Trading Bot Scheduler..."
echo "The bot will run at: 00:00, 06:00, 12:00, 18:00 EST/EDT"
echo ""

# Run the scheduler
python scheduler.py
