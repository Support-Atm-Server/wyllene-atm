"""
Wyllene Enterprise Bank - Database Layer
Handles all SQLite operations with clean, reusable functions.
"""
import sqlite3
from datetime import datetime
from config import DB_FILE, DEPARTMENTS, DEFAULT_USERS

def connect():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def initialize():
    """Create all tables and default data."""
    db = connect()
    c = db.cursor()
    
    # Users table
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, pin TEXT NOT NULL, security_answer TEXT DEFAULT '',
        role TEXT DEFAULT 'employee', department TEXT DEFAULT 'general',
        balance REAL DEFAULT 0.0, salary REAL DEFAULT 0.0,
        chat_id TEXT, email TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    
    # Transactions
    c.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, type TEXT,
        amount REAL, description TEXT, timestamp TEXT DEFAULT CURRENT_TIMESTAMP)""")
    
    # Audit log
    c.execute("""CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, action TEXT,
        details TEXT, timestamp TEXT DEFAULT CURRENT_TIMESTAMP)""")
    
    # CEO links
    c.execute("""CREATE TABLE IF NOT EXISTS ceo_links (
        ceo_username TEXT, employee_username TEXT, token TEXT UNIQUE, active INTEGER DEFAULT 1)""")
    
    # Approvals
    c.execute("""CREATE TABLE IF NOT EXISTS approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, type TEXT,
        amount REAL, status TEXT DEFAULT 'pending', timestamp TEXT DEFAULT CURRENT_TIMESTAMP)""")
    
    # Departments
    c.execute("""CREATE TABLE IF NOT EXISTS departments (
        name TEXT PRIMARY KEY, budget REAL DEFAULT 100000.0, manager TEXT DEFAULT '')""")
    
    # AI chat history
    c.execute("""CREATE TABLE IF NOT EXISTS ai_chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, question TEXT,
        response TEXT, timestamp TEXT DEFAULT CURRENT_TIMESTAMP)""")
    
    # Insert defaults
    for dept in DEPARTMENTS:
        c.execute("INSERT OR IGNORE INTO departments (name) VALUES (?)", (dept,))
    
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        for user in DEFAULT_USERS:
            c.execute("""INSERT INTO users (username, pin, security_answer, role, department, balance, salary)
                         VALUES (?,?,?,?,?,?,?)""",
                      (user["username"], user["pin"], user["security"],
                       user["role"], user["department"], user["balance"], user["salary"]))
    
    db.commit()
    db.close()
    print("✅ Database ready")

# ----- User Operations -----
def get_user(username):
    db = connect()
    row = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    db.close()
    return dict(row) if row else None

def get_all_users():
    db = connect()
    rows = db.execute("SELECT * FROM users").fetchall()
    db.close()
    return {row["username"]: dict(row) for row in rows}

def update_user(username, data):
    db = connect()
    db.execute("""UPDATE users SET pin=?, security_answer=?, role=?, department=?,
                  balance=?, salary=?, chat_id=?, email=? WHERE username=?""",
               (data.get("pin",""), data.get("security_answer",""), data.get("role","employee"),
                data.get("department","general"), data.get("balance",0.0), data.get("salary",0.0),
                data.get("chat_id",""), data.get("email",""), username))
    db.commit()
    db.close()

# ----- Transaction Operations -----
def add_transaction(username, txn_type, amount, description=""):
    db = connect()
    db.execute("INSERT INTO transactions (username, type, amount, description) VALUES (?,?,?,?)",
               (username, txn_type, amount, description))
    db.commit()
    db.close()

def get_transactions(username, limit=10):
    db = connect()
    rows = db.execute("SELECT * FROM transactions WHERE username=? ORDER BY id DESC LIMIT ?",
                      (username, limit)).fetchall()
    db.close()
    return [dict(row) for row in rows]

# ----- Audit Operations -----
def add_audit(username, action, details=""):
    db = connect()
    db.execute("INSERT INTO audit_log (username, action, details) VALUES (?,?,?)",
               (username, action, details))
    db.commit()
    db.close()

def get_audit_logs(limit=50):
    db = connect()
    rows = db.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    db.close()
    return [dict(row) for row in rows]

# ----- CEO Link Operations -----
def create_link(ceo, employee, token):
    db = connect()
    try:
        db.execute("INSERT INTO ceo_links (ceo_username, employee_username, token) VALUES (?,?,?)",
                   (ceo, employee, token))
        db.commit()
        return True
    except:
        return False
    finally:
        db.close()

def get_link(token):
    db = connect()
    row = db.execute("SELECT * FROM ceo_links WHERE token=? AND active=1", (token,)).fetchone()
    db.close()
    return dict(row) if row else None

# ----- AI Chat Operations -----
def save_chat(username, question, response):
    db = connect()
    db.execute("INSERT INTO ai_chats (username, question, response) VALUES (?,?,?)",
               (username, question, response))
    db.commit()
    db.close()

def get_chat_history(username, limit=10):
    db = connect()
    rows = db.execute("SELECT * FROM ai_chats WHERE username=? ORDER BY id DESC LIMIT ?",
                      (username, limit)).fetchall()
    db.close()
    return [dict(row) for row in rows]
