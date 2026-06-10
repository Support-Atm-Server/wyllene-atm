#!/bin/bash
cd ~/Documents/atm_project
fuser -k 9999/tcp 2>/dev/null
fuser -k 5000/tcp 2>/dev/null
export BOT_TOKEN="8980273422:AAG7c84_OTsFSXnWGLzF-2nSGd8mOfrS0eA"
python3 server_full.py &
sleep 2
python3 button_bot.py
