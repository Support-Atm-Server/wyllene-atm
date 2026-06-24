"""
Wyllene Enterprise Bank - Configuration
All settings are centralized here for easy management.
"""
import os

# ----- Server -----
HOST = "0.0.0.0"
SOCKET_PORT = 9999
WEB_PORT = int(os.environ.get("PORT", 5000))

# ----- Telegram -----
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8980273422:AAG7c84_OTsFSXnWGLzF-2nSGd8mOfrS0eA")

# ----- Database -----
DB_FILE = "atm.db"

# ----- Security -----
APPROVAL_THRESHOLD = 50000  # Amount needing CEO approval
MAX_LOGIN_ATTEMPTS = 3
SESSION_TIMEOUT = 3600  # 1 hour

# ----- Roles -----
ROLES = ["ceo", "manager", "employee", "auditor"]
DEPARTMENTS = ["Executive", "Engineering", "Sales", "HR", "Finance"]

# ----- Default Users (created on first run) -----
DEFAULT_USERS = [
    {"username": "ceo_wyllene", "pin": "9999", "security": "gold", "role": "ceo", "department": "Executive", "balance": 1000000.0, "salary": 500000.0},
    {"username": "manager_support", "pin": "8888", "security": "silver", "role": "manager", "department": "Engineering", "balance": 100000.0, "salary": 120000.0},
    {"username": "employee_dev", "pin": "7777", "security": "blue", "role": "employee", "department": "Engineering", "balance": 10000.0, "salary": 80000.0},
]

# ----- AI -----
AI_MODEL = "llama3.2:1b"  # Ollama model
AI_ENABLED = True
