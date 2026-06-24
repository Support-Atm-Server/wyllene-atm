"""
Wyllene Enterprise Bank - Main Server
Flask web server + Socket server for Telegram bot communication.
"""
import os
import json
import socket
import threading
import time
import secrets
from flask import Flask, request, jsonify, send_from_directory
from config import HOST, SOCKET_PORT, WEB_PORT, APPROVAL_THRESHOLD
from database import *
from fraud_detector import detector
from currency import currency_mgr, FIAT_CURRENCIES, CRYPTO_CURRENCIES

app = Flask(__name__)

# ----- Flask Routes -----
@app.route('/')
def dashboard():
    users = get_all_users()
    total = sum(u['balance'] for u in users.values())
    html = ['<!DOCTYPE html><html><head><title>Wyllene Enterprise Bank</title>',
            '<style>body{font-family:system-ui;margin:20px;background:#0a0a1a;color:#fff}',
            'table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:12px}',
            'th{background:#1a1a3a}.ceo{color:gold}.manager{color:silver}.employee{color:#4CAF50}',
            '.card{background:#1a1a3a;padding:20px;border-radius:10px;margin:10px 0}</style></head><body>',
            '<h1>🏢 Wyllene Enterprise Banking</h1>',
            f'<div class="card"><h2>Overview</h2><p>Total Assets: <b>${total:,.2f}</b> | Users: <b>{len(users)}</b></p>',
            '<p><a href="/chat" style="color:gold">💬 Open AI Chatbox</a></p></div>',
            '<h2>Employees</h2><table><tr><th>Username</th><th>Role</th><th>Department</th><th>Balance</th><th>Salary</th></tr>']
    for u, d in users.items():
        role = d.get('role','employee')
        html.append(f'<tr class="{role}"><td>{u}</td><td>{role.upper()}</td><td>{d.get("department","")}</td><td>${d["balance"]:,.2f}</td><td>${d.get("salary",0):,.2f}</td></tr>')
    html.append('</table></body></html>')
    return '\n'.join(html)

@app.route('/chat')
def chat():
    return send_from_directory('templates', 'chat.html')

@app.route('/fraud')
def fraud_dashboard():
    """Fraud detection dashboard."""
    from flask import render_template_string
    report = detector.get_fraud_report(7)
    
    html = '<!DOCTYPE html><html><head><title>Fraud Detection</title>'
    html += '<style>body{font-family:system-ui;margin:20px;background:#0a0a1a;color:#fff}'
    html += 'table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:12px}'
    html += 'th{background:#1a1a3a}.high{background:rgba(255,0,0,0.2)}.medium{background:rgba(255,165,0,0.2)}'
    html += '.low{background:rgba(255,255,0,0.1)}.safe{color:#4CAF50}</style></head><body>'
    html += '<h1>🛡️ Wyllene Fraud Detection</h1>'
    html += f'<p>Last 7 days — {len(report)} flagged transactions</p>'
    html += '<table><tr><th>Time</th><th>User</th><th>Type</th><th>Amount</th><th>Risk</th><th>Flags</th><th>Status</th></tr>'
    
    for txn in report:
        score = txn.get("risk_score", 0)
        css = "high" if score >= 70 else "medium" if score >= 40 else "low"
        html += f'<tr class="{css}"><td>{txn["timestamp"]}</td><td>{txn["username"]}</td><td>{txn["type"]}</td>'
        html += f'<td>${txn["amount"]:,.2f}</td><td>{score}/100</td>'
        html += f'<td>{" | ".join(txn.get("flags",[]))}</td><td>{txn.get("status","")}</td></tr>'
    
    html += '</table></body></html>'
    return html

@app.route('/currency')
def currency_dashboard():
    """Multi-currency dashboard."""
    users = get_all_users()
    fiat_rates = currency_mgr.get_fiat_rates()
    crypto_prices = currency_mgr.get_crypto_prices()
    
    html = '<!DOCTYPE html><html><head><title>Wyllene Currency</title>'
    html += '<style>body{font-family:system-ui;margin:20px;background:#0a0a1a;color:#fff}'
    html += 'table{border-collapse:collapse;width:100%;margin:10px 0}th,td{border:1px solid #333;padding:12px}'
    html += 'th{background:#1a1a3a}.card{background:#1a1a3a;padding:20px;border-radius:10px;margin:10px 0}'
    html += '.crypto{color:gold}.fiat{color:#4CAF50}</style></head><body>'
    html += '<h1>🌍 Wyllene Multi-Currency</h1>'
    
    # Live rates
    html += '<div class="card"><h2>💱 Live Exchange Rates (USD Base)</h2><table><tr><th>Currency</th><th>Rate</th></tr>'
    for code, rate in fiat_rates.items():
        if code in FIAT_CURRENCIES:
            html += f'<tr><td>{FIAT_CURRENCIES[code]["symbol"]} {code} — {FIAT_CURRENCIES[code]["name"]}</td><td>{rate:.4f}</td></tr>'
    html += '</table></div>'
    
    # Crypto prices
    html += '<div class="card"><h2>🪙 Crypto Prices</h2><table><tr><th>Currency</th><th>Price (USD)</th></tr>'
    for code, price in crypto_prices.items():
        html += f'<tr><td>{CRYPTO_CURRENCIES[code]["symbol"]} {code} — {CRYPTO_CURRENCIES[code]["name"]}</td><td>${price:,.2f}</td></tr>'
    html += '</table></div>'
    
    # User balances
    html += '<h2>👥 User Balances</h2>'
    for u, d in users.items():
        fiat = currency_mgr.get_user_fiat_balances(u)
        crypto = currency_mgr.get_user_crypto_balances(u)
        html += f'<div class="card"><h3>{u}</h3>'
        html += '<b>Fiat:</b> '
        for code, bal in fiat.items():
            if bal > 0:
                html += f'{FIAT_CURRENCIES.get(code,{}).get("symbol","")}{bal:,.2f} {code} | '
        html += '<br><b>Crypto:</b> '
        for code, bal in crypto.items():
            if bal > 0:
                html += f'{CRYPTO_CURRENCIES[code]["symbol"]} {bal:.6f} {code} | '
        html += '</div>'
    
    html += '</body></html>'
    return html

@app.route('/api/health')
def health():
    return jsonify({"status":"ok","version":"3.0.0"})

# ----- Socket Server -----
def handle_client(conn, addr):
    auth = False; username = None; user_data = None
    try:
        while True:
            data = conn.recv(8192)
            if not data: break
            req = json.loads(data.decode())
            cmd = req.get("cmd",""); resp = {}
            
            if cmd == "LOGIN":
                u = req.get("username","").strip().lower()
                p = req.get("pin","")
                a = req.get("security_answer","").lower()
                user = get_user(u)
                if user and user["pin"] == p and user.get("security_answer","") == a:
                    auth = True; username = u; user_data = user
                    resp = {"status":"ok","role":user["role"],"balance":user["balance"],"department":user["department"]}
                    add_audit(u, "LOGIN")
                else: resp = {"status":"error","message":"Invalid credentials"}
            
            elif not auth: resp = {"status":"error","message":"Not authenticated"}
            
            elif cmd == "BALANCE":
                user = get_user(username)
                resp = {"status":"ok","balance":user["balance"]}
            
            elif cmd == "DEPOSIT":
                amt = float(req.get("amount",0))
                if amt <= 0: resp = {"status":"error","message":"Invalid amount"}
                else:
                    user = get_user(username); user["balance"] += amt
                    update_user(username, user); add_transaction(username, "DEPOSIT", amt)
                    add_audit(username, "DEPOSIT", f"${amt:,.2f}")
                    fraud = detector.analyze_transaction(username, amt, "DEPOSIT")
                    resp = {"status":"ok","new_balance":user["balance"]}
                    if fraud["risk_score"] >= 40:
                        resp["fraud_alert"] = fraud
            
            elif cmd == "WITHDRAW":
                amt = float(req.get("amount",0))
                user = get_user(username)
                if amt <= 0 or amt > user["balance"]: resp = {"status":"error","message":"Insufficient funds"}
                elif amt > APPROVAL_THRESHOLD and user["role"] != "ceo":
                    db = connect()
                    db.execute("INSERT INTO approvals (username, type, amount) VALUES (?,?,?)", (username, "WITHDRAW", amt))
                    db.commit(); db.close()
                    resp = {"status":"pending_approval","message":f"${amt:,.2f} needs CEO approval"}
                else:
                    user["balance"] -= amt; update_user(username, user)
                    add_transaction(username, "WITHDRAW", amt); add_audit(username, "WITHDRAW", f"${amt:,.2f}")
                    fraud = detector.analyze_transaction(username, amt, "DEPOSIT")
                    resp = {"status":"ok","new_balance":user["balance"]}
                    if fraud["risk_score"] >= 40:
                        resp["fraud_alert"] = fraud
            
            elif cmd == "TRANSFER":
                target = req.get("recipient","").strip().lower()
                amt = float(req.get("amount",0))
                sender = get_user(username); recipient = get_user(target)
                if not recipient: resp = {"status":"error","message":"Recipient not found"}
                elif amt <= 0 or amt > sender["balance"]: resp = {"status":"error","message":"Insufficient funds"}
                else:
                    sender["balance"] -= amt; recipient["balance"] += amt
                    update_user(username, sender); update_user(target, recipient)
                    add_transaction(username, "TRANSFER_OUT", amt, f"To: {target}")
                    add_transaction(target, "TRANSFER_IN", amt, f"From: {username}")
                    add_audit(username, "TRANSFER", f"${amt:,.2f} to {target}")
                    resp = {"status":"ok","new_balance":sender["balance"]}
            
            elif cmd == "HISTORY":
                resp = {"status":"ok","history":get_transactions(username, 10)}
            
            elif cmd == "LIST_EMPLOYEES":
                if user_data["role"] not in ("ceo","manager"): resp = {"status":"error","message":"Permission denied"}
                else:
                    users = get_all_users()
                    emps = [{"username":u,"role":d["role"],"department":d["department"],"balance":d["balance"]} for u,d in users.items() if d["role"]!="ceo"]
                    resp = {"status":"ok","employees":emps}
            
            elif cmd == "PROCESS_PAYROLL":
                if user_data["role"] != "ceo": resp = {"status":"error","message":"CEO only"}
                else:
                    users = get_all_users(); processed = []
                    for u, d in users.items():
                        if d.get("salary",0) > 0:
                            d["balance"] += d["salary"]; update_user(u, d)
                            add_transaction(u, "SALARY", d["salary"]); add_audit("SYSTEM", "PAYROLL", f"{u}: ${d['salary']:,.2f}")
                            processed.append(f"{u}: +${d['salary']:,.2f}")
                    resp = {"status":"ok","processed":processed}
            
            elif cmd == "VIEW_AUDIT_LOG":
                if user_data["role"] != "ceo": resp = {"status":"error","message":"CEO only"}
                else: resp = {"status":"ok","logs":get_audit_logs(50)}
            
            elif cmd == "GENERATE_LINK_TOKEN":
                emp = req.get("employee","").strip().lower()
                token = secrets.token_hex(8)
                if create_link(username, emp, token): resp = {"status":"ok","token":token,"employee":emp}
                else: resp = {"status":"error","message":"Link exists"}
            
            elif cmd == "LINK_ACCOUNT":
                link = get_link(req.get("token",""))
                if link: resp = {"status":"ok","message":f"Linked to CEO: {link['ceo_username']}"}
                else: resp = {"status":"error","message":"Invalid token"}
            
            elif cmd == "SET_CHAT_ID":
                user = get_user(username)
                if user: user["chat_id"] = req.get("chat_id",""); update_user(username, user)
                resp = {"status":"ok"}
            
            elif cmd == "AI_CHAT":
                try:
                    from ai_assistant import ai
                    question = req.get("question","")
                    response = ai.ask(question, username)
                    save_chat(username, question, response)
                    resp = {"status":"ok","response":response}
                except Exception as e:
                    resp = {"status":"error","message":str(e)}
            
            elif cmd == "FIAT_RATES":
                resp = {"status":"ok","rates":currency_mgr.get_fiat_rates()}
            elif cmd == "CRYPTO_PRICES":
                resp = {"status":"ok","prices":currency_mgr.get_crypto_prices()}
            elif cmd == "FIAT_CONVERT":
                resp = currency_mgr.convert_fiat(username,
                    request.get("from","USD"), request.get("to","USD"), float(request.get("amount",0)))
            elif cmd == "CRYPTO_BUY":
                resp = currency_mgr.buy_crypto(username,
                    request.get("crypto","BTC"), float(request.get("amount",0)))
            elif cmd == "CRYPTO_SELL":
                resp = currency_mgr.sell_crypto(username,
                    request.get("crypto","BTC"), float(request.get("amount",0)))
            elif cmd == "MY_BALANCES":
                resp = {
                    "status": "ok",
                    "fiat": currency_mgr.get_user_fiat_balances(username),
                    "crypto": currency_mgr.get_user_crypto_balances(username)
                }
            else: resp = {"status":"error","message":"Unknown command"}
            
            conn.sendall(json.dumps(resp).encode())
    except Exception as e:
        print(f"Socket error: {e}")
    finally:
        conn.close()

def start_socket():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, SOCKET_PORT))
    server.listen(5)
    print(f"🔌 Socket server on port {SOCKET_PORT}")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

# ----- Main -----
if __name__ == "__main__":
    print("🏢 Wyllene Enterprise Bank Starting...")
    initialize()
    
    threading.Thread(target=start_socket, daemon=True).start()
    
    def start_bot():
        time.sleep(5)
        import bot
        bot.WylleneBot().run()
    threading.Thread(target=start_bot, daemon=True).start()
    
    app.run(host="0.0.0.0", port=WEB_PORT)
