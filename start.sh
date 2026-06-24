#!/bin/bash
cd ~/Documents/atm_project
python3 server_enterprise.py &
sleep 15
python3 button_bot.py
