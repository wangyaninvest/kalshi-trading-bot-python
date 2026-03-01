#!/bin/bash
# Installs the Kalshi trading bot as a macOS LaunchAgent so it:
#   - Starts automatically on login / system restart
#   - Auto-restarts on crashes
#   - Runs under caffeinate to prevent sleep/hibernation from stopping it

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_LABEL="com.kalshi.trading-bot"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_LABEL.plist"
LOG_DIR="$SCRIPT_DIR/logs"
PYTHON3_PATH="$(which python3)"

# Create logs directory
mkdir -p "$LOG_DIR"

echo "Installing Kalshi Trading Bot as a macOS LaunchAgent..."

# Generate the plist
cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/caffeinate</string>
        <string>-s</string>
        <string>$PYTHON3_PATH</string>
        <string>$SCRIPT_DIR/scheduler.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/bot.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/bot-error.log</string>
</dict>
</plist>
EOF

# Unload any existing instance before reloading
launchctl unload "$PLIST_PATH" 2>/dev/null || true

# Load (and start) the agent
launchctl load "$PLIST_PATH"

echo ""
echo "Trading bot installed and running."
echo "  Label:       $PLIST_LABEL"
echo "  Logs:        $LOG_DIR/bot.log"
echo "  Error logs:  $LOG_DIR/bot-error.log"
echo ""
echo "Useful commands:"
echo "  Check status:  launchctl list | grep kalshi"
echo "  Stop bot:      launchctl unload $PLIST_PATH"
echo "  View logs:     tail -f $LOG_DIR/bot.log"
