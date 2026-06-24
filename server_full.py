import os, sqlite3, json, socket, threading, time
from datetime import datetime
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
        balance REAL DEFAULT 0.0, chat_id TEXT)''')
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

def save_user(username, data):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE users SET pin=?, security_a=?, balance=?, chat_id=? WHERE username=?",
              (data['pin'], data['security_a'], data['balance'], data.get('chat_id',''), username))
    conn.commit(); conn.close()

def record_txn(username, ttype, amount):
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT INTO transactions (username, type, amount, timestamp) VALUES (?,?,?,?)",
              (username, ttype, amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit(); conn.close()

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

# ---------- Socket Server ----------
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
    except: pass
    finally: conn.close()

def start_socket():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 9999))
    server.listen(5)
    print("Socket server on port 9999")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

# ---------- Telegram Bot (simple) ----------
def start_bot():
    time.sleep(5)
    import button_bot
    button_bot.main()

# ---------- Main ----------
if __name__ == "__main__":
    init_db()
    threading.Thread(target=start_socket, daemon=True).start()
    threading.Thread(target=start_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting Flask on port {port}")
    app.run(host='0.0.0.0', port=port)
