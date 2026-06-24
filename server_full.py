import json, socket, threading, time, os, sqlite3
from datetime import datetime
from flask import Flask

HOST = '0.0.0.0'
PORT = 9999
WEB_PORT = int(os.environ.get("PORT", 5000))

def get_db():
    return sqlite3.connect("atm.db")

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, pin TEXT, security_a TEXT DEFAULT '',
        balance REAL DEFAULT 0.0, chat_id TEXT, email TEXT,
        two_factor INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, type TEXT,
        amount REAL, timestamp TEXT, running_balance REAL)''')
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, pin, security_a, balance) VALUES ('wyllene','1234','blue',1000.0)")
    conn.commit(); conn.close()

def load_users():
    conn = get_db(); conn.row_factory = sqlite3.Row
    c = conn.cursor(); c.execute("SELECT * FROM users")
    users = {row['username']: dict(row) for row in c.fetchall()}; conn.close()
    return users

def save_user(username, data):
    conn = get_db(); c = conn.cursor()
    c.execute('''UPDATE users SET pin=?, security_a=?, balance=?, chat_id=?, email=?, two_factor=?
                 WHERE username=?''',
              (data.get('pin',''), data.get('security_a',''), data.get('balance',0.0),
               data.get('chat_id',''), data.get('email',''), data.get('two_factor',0), username))
    conn.commit(); conn.close()

def record_txn(username, ttype, amount):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO transactions (username, type, amount, timestamp, running_balance) VALUES (?,?,?,?, (SELECT balance FROM users WHERE username=?))",
              (username, ttype, amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username))
    conn.commit(); conn.close()

# ---------- Flask Web Dashboard ----------
web_app = Flask(__name__)

@web_app.route('/')
def dashboard():
    users = load_users()
    total = sum(u['balance'] for u in users.values())
    html = "<h1>🏦 Wyllene ATM</h1><table border='1'><tr><th>User</th><th>Balance</th></tr>"
    for u, d in users.items():
        html += f"<tr><td>{u}</td><td>${d['balance']:.2f}</td></tr>"
    html += f"<tr><td><b>Total</b></td><td><b>${total:.2f}</b></td></tr></table>"
    return html

@web_app.route('/test')
def test():
    return "Wyllene ATM web server is running!"

def start_web():
    web_app.run(host='0.0.0.0', port=WEB_PORT, debug=False, use_reloader=False)

# ---------- Socket Server (simplified) ----------
def handle_client(conn, addr):
    auth = False; uname = None
    try:
        while True:
            data = conn.recv(4096)
            if not data: break
            req = json.loads(data.decode())
            cmd = req.get("cmd"); resp = {}
            if cmd == "LOGIN":
                u = req.get("username"); p = req.get("pin")
                users = load_users()
                if u == "admin" and p == "admin123":
                    auth = True; uname = "admin"; resp = {"status":"ok","admin":True}
                elif u in users and users[u]['pin'] == p:
                    if users[u].get('security_a','') == req.get("security_answer","").lower():
                        auth = True; uname = u
                        resp = {"status":"ok","balance":users[u]['balance']}
                    else: resp = {"status":"error","message":"Wrong security answer"}
                else: resp = {"status":"error","message":"Invalid credentials"}
            elif not auth: resp = {"status":"error","message":"Not authenticated"}
            elif cmd == "BALANCE":
                resp = {"status":"ok","balance":load_users()[uname]['balance']}
            elif cmd == "DEPOSIT":
                amt = float(req.get("amount",0))
                if amt <= 0: resp = {"status":"error","message":"Invalid amount"}
                else:
                    users = load_users(); users[uname]['balance'] += amt
                    save_user(uname, users[uname]); record_txn(uname, "DEPOSIT", amt)
                    resp = {"status":"ok","new_balance":users[uname]['balance']}
            elif cmd == "WITHDRAW":
                amt = float(req.get("amount",0))
                users = load_users()
                if amt <= 0 or amt > users[uname]['balance']:
                    resp = {"status":"error","message":"Insufficient funds"}
                else:
                    users[uname]['balance'] -= amt; save_user(uname, users[uname])
                    record_txn(uname, "WITHDRAW", amt)
                    resp = {"status":"ok","new_balance":users[uname]['balance']}
            elif cmd == "HISTORY":
                conn = get_db(); c = conn.cursor()
                c.execute("SELECT type, amount, timestamp FROM transactions WHERE username=? ORDER BY id DESC LIMIT 10", (uname,))
                hist = [{"type":r[0],"amount":r[1],"time":r[2]} for r in c.fetchall()]; conn.close()
                resp = {"status":"ok","history":hist}
            elif cmd == "SET_CHAT_ID":
                users = load_users(); users[uname]['chat_id'] = req.get("chat_id")
                save_user(uname, users[uname]); resp = {"status":"ok"}
            else: resp = {"status":"error","message":"Unknown command"}
            conn.sendall(json.dumps(resp).encode())
    except Exception as e: print(f"Socket error: {e}")
    finally: conn.close()

# ---------- Telegram Bot (simplified) ----------
def start_bot():
    """Run the bot in a separate thread."""
    time.sleep(8)   # wait for the server to be ready
    import button_bot
    button_bot.main()

# ---------- Main Server Start ----------
def start_server():
    init_db()
    threading.Thread(target=start_web, daemon=True).start()
    threading.Thread(target=start_bot, daemon=True).start()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"🏦 Server + Web running on port {PORT} (web: {WEB_PORT})")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()
