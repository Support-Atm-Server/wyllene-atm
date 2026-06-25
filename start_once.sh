#!/bin/bash

# Kill any existing instances FIRST
pkill -9 -f "python3 server.py" 2>/dev/null
pkill -9 -f "python3 bot.py" 2>/dev/null
sleep 2

# Clear Telegram queue
curl -s "https://api.telegram.org/bot8980273422:AAG7c84_OTsFSXnWGLzF-2nSGd8mOfrS0eA/getUpdates?offset=-1" > /dev/null

# Start server
echo "🏢 Starting server..."
python3 server.py &
SERVER_PID=$!
sleep 8

# Verify server is the ONLY one
if [ $(ps aux | grep -c "server.py") -gt 2 ]; then
    echo "❌ Multiple servers detected! Aborting."
    sudo pkill -9 python3
    exit 1
fi

# Start bot
echo "🤖 Starting bot..."
python3 bot.py

# Cleanup on exit
kill $SERVER_PID 2>/dev/null
