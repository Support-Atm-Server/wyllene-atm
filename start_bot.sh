#!/bin/bash
cd ~/Documents/atm_project
fuser -k 9999/tcp 2>/dev/null
python3 server_full.py &
sleep 2
python3 button_bot.py
