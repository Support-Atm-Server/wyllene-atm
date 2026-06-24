"""Wyllene ATM Enterprise Server."""
import os
import json
import socket
import threading
import time
import secrets
from datetime import datetime
from flask import Flask, jsonify
from config import HOST, SOCKET_PORT, WEB_PORT, APPROVAL_THRESHOLD
from database import (
    init_database, get_user, get_all_users, update_user,
    add_transaction, get_transactions, add_audit_log, get_audit_logs,
    create_ceo_link, get_ceo_link, add_approval
)

app = Flask(__name__)

# ============= FLASK ROUTES =============
@app.route('/')
def dashboard():
    """Enterprise web dashboard."""
    users = get_all_users()
    total = sum(u['balance'] for u in users.values())
    
    html = """<!DOCTYPE html>
<html><head><title>Wyllene Enterprise Bank</title>
<style>
body{font-family:system-ui;margin:20px;background:#0a0a1a;color:#fff}
table{border-collapse:collapse;width:100%;margin:10px 0}
th,td{border:1px solid #333;padding:12px;text-align:left}
th{background:#1a1a3a}
.ceo{color:gold;font-weight:bold}
.manager{color:silver}
.employee{color:#4CAF50}
.card{background:#1a1a3a;padding:20px;border-radius:10px;margin:10px 0}
</style></head><body>
<h1>🏢 Wyllene Enterprise Banking</h1>"""
    
    html += f'<div class="card"><h2>Company Overview</h2><p>Total Assets: <b>${total:,.2f}</b> | Users: <b>{len(users)}</b></p></div>'
    
    html += '<h2>Employees</h2><table><tr><th>Username</th><th>Role</th><th>Department</th><th>Balance</th><th>Salary</th></tr>'
    for u, d in users.items():
        role_class = d.get('role', 'employee')
        html += f'<tr class="{role_class}"><td>{u}</td><td>{d.get("role","employee").upper()}</td><td>{d.get("department","general")}</td><td>${d["balance"]:,.2f}</td><td>${d.get("salary",0):,.2f}</td></tr>'
    html += '</table></body></html>'
    return html

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "version": "2.0.0"})

# ============= SOCKET SERVER =============
def handle_client(conn, addr):
    """Handle a single client connection."""
    authenticated = False
    username = None
    user_data = None
    
    try:
        while True:
            data = conn.recv(8192)
            if not data:
                break
            
            request = json.loads(data.decode())
            cmd = request.get("cmd", "")
            response = {}
            
            # ---- AUTHENTICATION ----
            if cmd == "LOGIN":
                u = request.get("username", "").strip().lower()
                p = request.get("pin", "")
                answer = request.get("security_answer", "").lower()
                
                user = get_user(u)
                if user and user['pin'] == p:
                    if user.get('security_answer', '') == answer:
                        authenticated = True
                        username = u
                        user_data = user
                        response = {
                            "status": "ok",
                            "role": user['role'],
                            "balance": user['balance'],
                            "department": user['department']
                        }
                        add_audit_log(u, "LOGIN")
                    else:
                        response = {"status": "error", "message": "Wrong security answer"}
                else:
                    response = {"status": "error", "message": "Invalid credentials"}
            
            elif not authenticated:
                response = {"status": "error", "message": "Not authenticated"}
            
            # ---- BALANCE ----
            elif cmd == "BALANCE":
                user = get_user(username)
                response = {"status": "ok", "balance": user['balance']}
            
            # ---- DEPOSIT ----
            elif cmd == "DEPOSIT":
                amount = float(request.get("amount", 0))
                if amount <= 0:
                    response = {"status": "error", "message": "Invalid amount"}
                else:
                    user = get_user(username)
                    user['balance'] += amount
                    update_user(username, user)
                    add_transaction(username, "DEPOSIT", amount)
                    add_audit_log(username, "DEPOSIT", f"${amount:,.2f}")
                    response = {"status": "ok", "new_balance": user['balance']}
            
            # ---- WITHDRAW ----
            elif cmd == "WITHDRAW":
                amount = float(request.get("amount", 0))
                user = get_user(username)
                
                if amount <= 0 or amount > user['balance']:
                    response = {"status": "error", "message": "Insufficient funds"}
                elif amount > APPROVAL_THRESHOLD and user['role'] != 'ceo':
                    add_approval(username, "WITHDRAW", amount)
                    response = {
                        "status": "pending_approval",
                        "message": f"Withdrawal of ${amount:,.2f} requires CEO approval"
                    }
                else:
                    user['balance'] -= amount
                    update_user(username, user)
                    add_transaction(username, "WITHDRAW", amount)
                    add_audit_log(username, "WITHDRAW", f"${amount:,.2f}")
                    response = {"status": "ok", "new_balance": user['balance']}
            
            # ---- TRANSFER ----
            elif cmd == "TRANSFER":
                target = request.get("recipient", "").strip().lower()
                amount = float(request.get("amount", 0))
                sender = get_user(username)
                recipient = get_user(target)
                
                if not recipient:
                    response = {"status": "error", "message": "Recipient not found"}
                elif amount <= 0 or amount > sender['balance']:
                    response = {"status": "error", "message": "Insufficient funds"}
                else:
                    sender['balance'] -= amount
                    recipient['balance'] += amount
                    update_user(username, sender)
                    update_user(target, recipient)
                    add_transaction(username, "TRANSFER_OUT", amount, f"To: {target}")
                    add_transaction(target, "TRANSFER_IN", amount, f"From: {username}")
                    add_audit_log(username, "TRANSFER", f"${amount:,.2f} to {target}")
                    response = {"status": "ok", "new_balance": sender['balance']}
            
            # ---- HISTORY ----
            elif cmd == "HISTORY":
                history = get_transactions(username, 10)
                response = {"status": "ok", "history": history}
            
            # ---- LIST EMPLOYEES ----
            elif cmd == "LIST_EMPLOYEES":
                if user_data['role'] not in ('ceo', 'manager'):
                    response = {"status": "error", "message": "Insufficient permissions"}
                else:
                    users = get_all_users()
                    employees = [
                        {"username": u, "role": d['role'], "department": d['department'], "balance": d['balance']}
                        for u, d in users.items() if d['role'] != 'ceo'
                    ]
                    response = {"status": "ok", "employees": employees}
            
            # ---- PAYROLL ----
            elif cmd == "PROCESS_PAYROLL":
                if user_data['role'] != 'ceo':
                    response = {"status": "error", "message": "CEO only"}
                else:
                    users = get_all_users()
                    processed = []
                    for u, d in users.items():
                        if d.get('salary', 0) > 0:
                            d['balance'] += d['salary']
                            update_user(u, d)
                            add_transaction(u, "SALARY", d['salary'])
                            add_audit_log("SYSTEM", "PAYROLL", f"{u}: ${d['salary']:,.2f}")
                            processed.append(f"{u}: +${d['salary']:,.2f}")
                    response = {"status": "ok", "processed": processed}
            
            # ---- AUDIT LOG ----
            elif cmd == "VIEW_AUDIT_LOG":
                if user_data['role'] != 'ceo':
                    response = {"status": "error", "message": "CEO only"}
                else:
                    logs = get_audit_logs(50)
                    response = {"status": "ok", "logs": logs}
            
            # ---- API KEY ----
            elif cmd == "GENERATE_API_KEY":
                from database import get_connection
                key = secrets.token_hex(16)
                conn = get_connection()
                c = conn.cursor()
                c.execute("CREATE TABLE IF NOT EXISTS api_keys (key TEXT PRIMARY KEY, username TEXT)")
                c.execute("INSERT INTO api_keys (key, username) VALUES (?,?)", (key, username))
                conn.commit()
                conn.close()
                response = {"status": "ok", "api_key": key}
            
            # ---- CEO LINK ----
            elif cmd == "GENERATE_LINK_TOKEN":
                employee = request.get("employee", "").strip().lower()
                token = secrets.token_hex(8)
                if create_ceo_link(username, employee, token):
                    response = {"status": "ok", "token": token, "employee": employee}
                else:
                    response = {"status": "error", "message": "Link already exists"}
            
            elif cmd == "LINK_ACCOUNT":
                token = request.get("token", "")
                link = get_ceo_link(token)
                if link:
                    response = {"status": "ok", "message": f"Linked to CEO: {link['ceo_username']}"}
                else:
                    response = {"status": "error", "message": "Invalid token"}
            
            elif cmd == "SET_CHAT_ID":
                user = get_user(username)
                if user:
                    user['chat_id'] = request.get("chat_id", "")
                    update_user(username, user)
                response = {"status": "ok"}
            
            else:
                response = {"status": "error", "message": "Unknown command"}
            
            conn.sendall(json.dumps(response).encode())
    
    except Exception as e:
        print(f"Socket error: {e}")
    finally:
        conn.close()

def start_socket_server():
    """Start the socket server in a background thread."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, SOCKET_PORT))
    server.listen(5)
    print(f"🔌 Socket server on port {SOCKET_PORT}")
    
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

# ============= MAIN =============
if __name__ == "__main__":
    print("🏢 Wyllene Enterprise Bank Starting...")
    
    # Initialize database
    init_database()
    
    # Start socket server in background
    threading.Thread(target=start_socket_server, daemon=True).start()
    
    # Start bot in background
    def start_bot():
        time.sleep(5)
        import bot
        bot.WylleneBot().run()
    threading.Thread(target=start_bot, daemon=True).start()
    
    # Start Flask web server
    port = int(os.environ.get("PORT", WEB_PORT))
    print(f"🌐 Web dashboard on port {port}")
    app.run(host='0.0.0.0', port=port)
