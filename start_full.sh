#!/bin/bash
cd ~/Documents/atm_project
fuser -k 9999/tcp 2>/dev/null
fuser -k 5000/tcp 2>/dev/null
python3 server_full.py &
sleep 1
echo "Server + Web dashboard running. Open http://localhost:5000 in browser."
python3 atm_full.py
kill %1 2>/dev/null
