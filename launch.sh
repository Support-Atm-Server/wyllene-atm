#!/bin/bash
# Wyllene ATM Safe Launcher - prevents overlapping bots

LOCKFILE="/tmp/wyllene_bot.lock"
PROJECT_DIR="$HOME/Documents/atm_project"

# ---- Kill any existing instances ----
echo "🧹 Cleaning up old processes..."
pkill -f "python3 bot.py" 2>/dev/null
pkill -f "python3 server.py" 2>/dev/null
rm -f "$LOCKFILE"
sleep 2

# ---- Check if lock file exists (prevents double launch) ----
if [ -f "$LOCKFILE" ]; then
    echo "❌ Another instance is already running!"
    echo "   If you're sure it's not, run: rm -f $LOCKFILE"
    exit 1
fi

# ---- Create lock file ----
touch "$LOCKFILE"

# ---- Cleanup function (runs on exit) ----
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    pkill -f "python3 server.py" 2>/dev/null
    rm -f "$LOCKFILE"
    echo "👋 Done."
}

# Ensure cleanup runs when script exits
trap cleanup EXIT INT TERM

# ---- Start the server (which starts the bot internally) ----
cd "$PROJECT_DIR"
echo "🏢 Starting Wyllene Enterprise Bank..."
python3 server.py

# The script will stay here until you press Ctrl+C
# Then it will automatically clean up
