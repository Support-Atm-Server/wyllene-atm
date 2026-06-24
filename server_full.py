import os, sqlite3
from flask import Flask

app = Flask(__name__)

# ---------- Database ----------
def get_db():
    return sqlite3.connect("atm.db")

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, pin TEXT, security_a TEXT DEFAULT '',
        balance REAL DEFAULT 0.0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, type TEXT,
        amount REAL, timestamp TEXT)''')
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, pin, security_a, balance) VALUES ('wyllene','1234','blue',1000.0)")
    conn.commit(); conn.close()

def load_users():
    conn = get_db(); conn.row_factory = sqlite3.Row
    c = conn.cursor(); c.execute("SELECT * FROM users")
    users = {row['username']: dict(row) for row in c.fetchall()}; conn.close()
    return users

# ---------- Flask Routes ----------
@app.route('/')
def dashboard():
    users = load_users()
    total = sum(u['balance'] for u in users.values())
    html = "<h1>🏦 Wyllene ATM</h1><table border='1'><tr><th>User</th><th>Balance</th></tr>"
    for u, d in users.items():
        html += f"<tr><td>{u}</td><td>${d['balance']:.2f}</td></tr>"
    html += f"<tr><td><b>Total</b></td><td><b>${total:.2f}</b></td></tr></table>"
    return html

@app.route('/test')
def test():
    return "OK"

# ---------- Start ----------
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting Flask on port {port}")
    app.run(host='0.0.0.0', port=port)
