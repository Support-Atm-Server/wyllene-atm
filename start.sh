#!/bin/bash
cd ~/Documents/atm_project
python3 server.py &
sleep 10
python3 bot.py
