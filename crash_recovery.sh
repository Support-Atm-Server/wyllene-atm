#!/bin/bash
# Wyllene Dynasty — Crash Recovery
cd ~/Documents/atm_project

# Check if server is running
if ! pgrep -f "python3 server.py" > /dev/null; then
    echo "[$(date)] Server down! Restarting..." >> logs/crash.log
    python3 server.py &
    echo "[$(date)] Server restarted" >> logs/crash.log
fi
