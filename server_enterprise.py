import os, sqlite3, json, socket, threading, time, secrets, hashlib
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)

# ---------- Database ----------
def get_db():
    return sqlite3.connect("atm_enterprise.db")

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # Users with roles
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE, pin TEXT, security_a TEXT DEFAULT '',
        role TEXT DEFAULT 'employee',
        department TEXT DEFAULT 'general',
        balance REAL DEFAULT 0.0,
        salary REAL DEFAULT 0.0,
        chat_id TEXT, email TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    
    # Departments with budgets
    c.execute('''CREATE TABLE IF NOT EXISTS departments (
        name TEXT PRIMARY KEY,
        budget REAL DEFAULT 0.0,
        manager_username TEXT)''')
    
    # Transactions with approval
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT, type TEXT, amount REAL,
        timestamp TEXT, status TEXT DEFAULT 'completed',
        approved_by TEXT, description TEXT)''')
    
    # Approval queue for large transactions
    c.execute('''CREATE TABLE IF NOT EXISTS approval_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT, type TEXT, amount REAL,
        timestamp TEXT, status TEXT DEFAULT 'pending',
        approved_by TEXT DEFAULT NULL)''')
    
    # Audit log
    c.execute('''CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT, action TEXT, details TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP)''')
    
    # API keys for external integrations
    c.execute('''CREATE TABLE IF NOT EXISTS api_keys (
        key TEXT PRIMARY KEY,
        username TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        active INTEGER DEFAULT 1)''')
    
    # CEO links (from previous feature)
    c.execute('''CREATE TABLE IF NOT EXISTS ceo_links (
        ceo_username TEXT, employee_username TEXT,
        token TEXT UNIQUE, active INTEGER DEFAULT 1)''')
    
    # Salary payments schedule
    c.execute('''CREATE TABLE IF NOT EXISTS payroll (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT, amount REAL, schedule_date TEXT,
        status TEXT DEFAULT 'pending')''')
    
    # Default departments
    for dept in ['Executive', 'Engineering', 'Sales', 'HR', 'Finance']:
        c.execute("INSERT OR IGNORE INTO departments (name, budget) VALUES (?, 100000.0)", (dept,))
    
    # Default CEO account
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute('''INSERT INTO users (username, pin, security_a, role, department, balance, salary)
                     VALUES ('ceo_wyllene', '9999', 'gold', 'ceo', 'Executive', 1000000.0, 500000.0)''')
        c.execute('''INSERT INTO users (username, pin, security_a, role, department, balance, salary)
                     VALUES ('manager_support', '8888', 'silver', 'manager', 'Engineering', 100000.0, 120000.0)''')
        c.execute('''INSERT INTO users (username, pin, security_a, role, department, balance, salary)
                     VALUES ('employee_dev', '7777', 'blue', 'employee', 'Engineering', 10000.0, 80000.0)''')
    
    conn.commit(); conn.close()

# ---------- Audit Helper ----------
def audit_log(username, action, details=""):
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT INTO audit_log (username, action, details) VALUES (?,?,?)",
              (username, action, details))
    conn.commit(); conn.close()

# ---------- User Helpers ----------
def load_user(username):
    conn = get_db(); conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    row = c.fetchone(); conn.close()
    return dict(row) if row else None

def load_all_users():
    conn = get_db(); conn.row_factory = sqlite3.Row
    c = conn.cursor(); c.execute("SELECT * FROM users")
    users = {row['username']: dict(row) for row in c.fetchall()}; conn.close()
    return users

def save_user(username, data):
    conn = get_db(); c = conn.cursor()
    c.execute('''UPDATE users SET pin=?, security_a=?, role=?, department=?,
                 balance=?, salary=?, chat_id=?, email=? WHERE username=?''',
              (data.get('pin',''), data.get('security_a',''), data.get('role','employee'),
               data.get('department','general'), data.get('balance',0.0),
               data.get('salary',0.0), data.get('chat_id',''), data.get('email',''), username))
    conn.commit(); conn.close()

# ---------- Enterprise Web Dashboard ----------
@app.route('/')
def enterprise_dashboard():
    users = load_all_users()
    total_assets = sum(u['balance'] for u in users.values())
    
    html = """<html><head><title>Wyllene Enterprise Bank</title>
    <style>body{font-family:Arial;margin:20px;background:#0a0a1a;color:#fff}
    table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:10px}
    th{background:#1a1a3a}.ceo{color:gold}.manager{color:silver}.employee{color:#4CAF50}</style></head><body>
    <h1>🏢 Wyllene Enterprise Banking</h1>"""
    
    # Company overview
    html += f"<h2>Company Overview</h2>"
    html += f"<p>Total Assets: <b>${total_assets:,.2f}</b> | Total Users: <b>{len(users)}</b></p>"
    
    # User table
    html += "<h2>Employees</h2><table><tr><th>Username</th><th>Role</th><th>Department</th><th>Balance</th><th>Salary</th></tr>"
    for u, d in users.items():
        role_class = d.get('role','employee')
        html += f"<tr class='{role_class}'><td>{u}</td><td>{d.get('role','employee').upper()}</td><td>{d.get('department','general')}</td><td>${d['balance']:,.2f}</td><td>${d.get('salary',0):,.2f}</td></tr>"
    html += "</table>"
    
    # Department budgets
    conn = get_db(); conn.row_factory = sqlite3.Row
    c = conn.cursor(); c.execute("SELECT * FROM departments")
    depts = c.fetchall(); conn.close()
    html += "<h2>Department Budgets</h2><table><tr><th>Department</th><th>Budget</th><th>Manager</th></tr>"
    for d in depts:
        html += f"<tr><td>{d['name']}</td><td>${d['budget']:,.2f}</td><td>{d['manager_username'] or 'Unassigned'}</td></tr>"
    html += "</table></body></html>"
    return html

@app.route('/api/health')
def health():
    return jsonify({"status":"ok","version":"enterprise"})

# ---------- Socket Server ----------
def handle_client(conn, addr):
    auth = False; uname = None; user_data = None
    try:
        while True:
            data = conn.recv(8192)
            if not data: break
            req = json.loads(data.decode())
            cmd = req.get("cmd"); resp = {}
            
            # Authentication
            if cmd == "LOGIN":
                u = req.get("username"); p = req.get("pin")
                user = load_user(u)
                if user and user['pin'] == p:
                    if user.get('security_a','') == req.get("security_answer","").lower():
                        auth = True; uname = u; user_data = user
                        resp = {"status":"ok","role":user['role'],"balance":user['balance'],
                                "department":user['department']}
                        audit_log(u, "LOGIN", f"Role: {user['role']}")
                    else: resp = {"status":"error","message":"Wrong security answer"}
                else: resp = {"status":"error","message":"Invalid credentials"}
            
            elif not auth: resp = {"status":"error","message":"Not authenticated"}
            
            # Balance
            elif cmd == "BALANCE":
                user = load_user(uname)
                resp = {"status":"ok","balance":user['balance']}
            
            # Deposit (all roles)
            elif cmd == "DEPOSIT":
                amt = float(req.get("amount",0))
                if amt <= 0: resp = {"status":"error","message":"Invalid amount"}
                else:
                    user = load_user(uname); user['balance'] += amt
                    save_user(uname, user)
                    audit_log(uname, "DEPOSIT", f"${amt:.2f}")
                    resp = {"status":"ok","new_balance":user['balance']}
            
            # Withdraw (requires approval for large amounts)
            elif cmd == "WITHDRAW":
                amt = float(req.get("amount",0))
                user = load_user(uname)
                if amt <= 0 or amt > user['balance']:
                    resp = {"status":"error","message":"Insufficient funds"}
                elif amt > 50000 and user['role'] != 'ceo':
                    # Requires approval
                    conn = get_db(); c = conn.cursor()
                    c.execute("INSERT INTO approval_queue (username, type, amount, timestamp) VALUES (?,?,?,?)",
                              (uname, "WITHDRAW", amt, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit(); conn.close()
                    resp = {"status":"pending_approval","message":f"Withdrawal of ${amt:.2f} requires CEO approval"}
                else:
                    user['balance'] -= amt; save_user(uname, user)
                    audit_log(uname, "WITHDRAW", f"${amt:.2f}")
                    resp = {"status":"ok","new_balance":user['balance']}
            
            # Transfer
            elif cmd == "TRANSFER":
                target = req.get("recipient"); amt = float(req.get("amount",0))
                user = load_user(uname)
                target_user = load_user(target)
                if not target_user: resp = {"status":"error","message":"Recipient not found"}
                elif amt <= 0 or amt > user['balance']: resp = {"status":"error","message":"Insufficient funds"}
                else:
                    user['balance'] -= amt; target_user['balance'] += amt
                    save_user(uname, user); save_user(target, target_user)
                    audit_log(uname, "TRANSFER", f"${amt:.2f} to {target}")
                    resp = {"status":"ok","new_balance":user['balance']}
            
            # View all employees (CEO/Manager only)
            elif cmd == "LIST_EMPLOYEES":
                if user_data['role'] not in ('ceo','manager'):
                    resp = {"status":"error","message":"Insufficient permissions"}
                else:
                    users = load_all_users()
                    emps = [{"username":u,"role":d['role'],"department":d['department'],
                             "balance":d['balance']} for u,d in users.items() if d['role'] != 'ceo']
                    resp = {"status":"ok","employees":emps}
            
            # Generate API key
            elif cmd == "GENERATE_API_KEY":
                key = secrets.token_hex(16)
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO api_keys (key, username) VALUES (?,?)", (key, uname))
                conn.commit(); conn.close()
                resp = {"status":"ok","api_key":key}
            
            # Payroll: process all pending salaries
            elif cmd == "PROCESS_PAYROLL":
                if user_data['role'] != 'ceo': resp = {"status":"error","message":"CEO only"}
                else:
                    users = load_all_users()
                    paid = []
                    for u, d in users.items():
                        if d.get('salary',0) > 0:
                            d['balance'] += d['salary']
                            save_user(u, d)
                            paid.append(f"{u}: +${d['salary']:,.2f}")
                            audit_log("SYSTEM", "PAYROLL", f"Paid {u} ${d['salary']:,.2f}")
                    resp = {"status":"ok","processed":paid}
            
            # Audit log view (CEO only)
            elif cmd == "VIEW_AUDIT_LOG":
                if user_data['role'] != 'ceo': resp = {"status":"error","message":"CEO only"}
                else:
                    conn = get_db(); conn.row_factory = sqlite3.Row
                    c = conn.cursor()
                    c.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 50")
                    logs = [dict(row) for row in c.fetchall()]; conn.close()
                    resp = {"status":"ok","logs":logs}
            
            # CEO link features (from previous)
            elif cmd == "GENERATE_LINK_TOKEN":
                emp = req.get("employee","").strip().lower()
                token = secrets.token_hex(8)
                conn = get_db(); c = conn.cursor()
                try:
                    c.execute("INSERT INTO ceo_links (ceo_username, employee_username, token) VALUES (?,?,?)",
                              (uname, emp, token))
                    conn.commit(); resp = {"status":"ok","token":token}
                except: resp = {"status":"error","message":"Link exists"}
                finally: conn.close()
            
            elif cmd == "LINK_ACCOUNT":
                token = req.get("token","")
                conn = get_db(); c = conn.cursor()
                c.execute("SELECT * FROM ceo_links WHERE token=? AND active=1", (token,))
                row = c.fetchone()
                if row: resp = {"status":"ok","message":f"Linked to CEO: {row[0]}","ceo":row[0]}
                else: resp = {"status":"error","message":"Invalid token"}
                conn.close()
            
            else: resp = {"status":"error","message":"Unknown command"}
            
            conn.sendall(json.dumps(resp).encode())
    except Exception as e: print(f"Socket error: {e}")
    finally: conn.close()

def start_socket():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 9999))
    server.listen(5)
    print("🔌 Enterprise socket server on port 9999")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

# ---------- Start ----------
if __name__ == "__main__":
    init_db()
    threading.Thread(target=start_socket, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    print(f"🏢 Wyllene Enterprise Bank starting on port {port}")
    app.run(host='0.0.0.0', port=port)
