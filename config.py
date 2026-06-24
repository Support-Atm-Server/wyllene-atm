"""Configuration settings for Wyllene ATM."""
import os

# Server
HOST = '0.0.0.0'
SOCKET_PORT = 9999
WEB_PORT = int(os.environ.get("PORT", 5000))

# Telegram
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8980273422:AAG7c84_OTsFSXnWGLzF-2nSGd8mOfrS0eA")
BOT_USERNAME = "@wylleneATM_bot"

# Database
DB_FILE = "atm.db"

# Default admin
ADMIN_USER = "admin"
ADMIN_PIN = "admin123"

# Roles
ROLES = ["ceo", "manager", "employee", "auditor"]
DEPARTMENTS = ["Executive", "Engineering", "Sales", "HR", "Finance"]

# Limits
APPROVAL_THRESHOLD = 50000  # Amount requiring CEO approval
