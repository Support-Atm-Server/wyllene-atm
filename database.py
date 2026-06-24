"""Database operations for Wyllene ATM."""
import sqlite3
from config import DB_FILE, DEPARTMENTS

def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize all database tables."""
    conn = get_connection()
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        pin TEXT NOT NULL,
        security_answer TEXT DEFAULT '',
        role TEXT DEFAULT 'employee',
        department TEXT DEFAULT 'general',
        balance REAL DEFAULT 0.0,
        salary REAL DEFAULT 0.0,
        chat_id TEXT,
        email TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Transactions
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        type TEXT,
        amount REAL,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        description TEXT DEFAULT ''
    )''')
    
    # CEO Links
    c.execute('''CREATE TABLE IF NOT EXISTS ceo_links (
        ceo_username TEXT,
        employee_username TEXT,
        token TEXT UNIQUE,
        active INTEGER DEFAULT 1
    )''')
    
    # Audit Log
    c.execute('''CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        action TEXT,
        details TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Approval Queue
    c.execute('''CREATE TABLE IF NOT EXISTS approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        type TEXT,
        amount REAL,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending'
    )''')
    
    # Departments
    c.execute('''CREATE TABLE IF NOT EXISTS departments (
        name TEXT PRIMARY KEY,
        budget REAL DEFAULT 100000.0,
        manager TEXT DEFAULT ''
    )''')
    
    # Insert default departments
    for dept in DEPARTMENTS:
        c.execute("INSERT OR IGNORE INTO departments (name) VALUES (?)", (dept,))
    
    # Insert default users if empty
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        default_users = [
            ("ceo_wyllene", "9999", "gold", "ceo", "Executive", 1000000.0, 500000.0),
            ("manager_support", "8888", "silver", "manager", "Engineering", 100000.0, 120000.0),
            ("employee_dev", "7777", "blue", "employee", "Engineering", 10000.0, 80000.0),
            ("wyllene", "1234", "blue", "employee", "general", 1000.0, 0.0)
        ]
        c.executemany(
            "INSERT INTO users (username, pin, security_answer, role, department, balance, salary) VALUES (?,?,?,?,?,?,?)",
            default_users
        )
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

# ---------- User Operations ----------
def get_user(username):
    """Get a single user by username."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_users():
    """Get all users."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = {row['username']: dict(row) for row in c.fetchall()}
    conn.close()
    return users

def update_user(username, data):
    """Update user fields."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''UPDATE users SET 
        pin=?, security_answer=?, role=?, department=?,
        balance=?, salary=?, chat_id=?, email=?
        WHERE username=?''',
        (data.get('pin',''), data.get('security_answer',''),
         data.get('role','employee'), data.get('department','general'),
         data.get('balance',0.0), data.get('salary',0.0),
         data.get('chat_id',''), data.get('email',''), username))
    conn.commit()
    conn.close()

# ---------- Transaction Operations ----------
def add_transaction(username, txn_type, amount, description=""):
    """Record a transaction."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO transactions (username, type, amount, description) VALUES (?,?,?,?)",
              (username, txn_type, amount, description))
    conn.commit()
    conn.close()

def get_transactions(username, limit=10):
    """Get recent transactions for a user."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM transactions WHERE username=? ORDER BY id DESC LIMIT ?", (username, limit))
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows

# ---------- Audit Operations ----------
def add_audit_log(username, action, details=""):
    """Add an audit log entry."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO audit_log (username, action, details) VALUES (?,?,?)",
              (username, action, details))
    conn.commit()
    conn.close()

def get_audit_logs(limit=50):
    """Get recent audit logs."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows

# ---------- CEO Link Operations ----------
def create_ceo_link(ceo, employee, token):
    """Create a CEO-employee link."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO ceo_links (ceo_username, employee_username, token) VALUES (?,?,?)",
                  (ceo, employee, token))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def get_ceo_link(token):
    """Get CEO link by token."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM ceo_links WHERE token=? AND active=1", (token,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

# ---------- Approval Operations ----------
def add_approval(username, txn_type, amount):
    """Add a transaction to approval queue."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO approvals (username, type, amount) VALUES (?,?,?)",
              (username, txn_type, amount))
    conn.commit()
    conn.close()
