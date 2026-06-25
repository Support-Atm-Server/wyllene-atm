#!/bin/bash
cd ~/Documents/atm_project

# Kill old processes
pkill -9 python3 2>/dev/null
sudo fuser -k 9999/tcp 2>/dev/null
sleep 2

# Start server
echo "🏢 Starting server..."
python3 server.py &
SERVER_PID=$!

# Wait for socket to be ready
echo "⏳ Waiting for socket server..."
for i in {1..20}; do
    if python3 -c "import socket; s=socket.socket(); s.connect(('localhost',9999)); s.close()" 2>/dev/null; then
        echo "✅ Socket ready"
        break
    fi
    sleep 2
done

# Start bot
echo "🤖 Starting bot..."
python3 bot.py

# Cleanup
kill $SERVER_PID 2>/dev/null
