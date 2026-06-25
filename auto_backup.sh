#!/bin/bash
# Wyllene Dynasty — Auto Backup Script
cd ~/Documents/atm_project
python3 -c "from bulletproof import backup_database; print(backup_database())"
