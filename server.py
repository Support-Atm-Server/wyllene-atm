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
            
            elif cmd == "USER_ANALYTICS":
                resp = {"status":"ok","stats":analytics.get_user_analytics(request.get("username",username))["stats"]}
            elif cmd == "TRANSACTION_SUMMARY":
                resp = {"status":"ok","summary":analytics.get_transaction_summary(30)}
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

@app.route('/family')
def family_home():
    """Family & Heirs Dashboard."""
    return """<!DOCTYPE html><html><head><title>Wyllene Dynasty — Family</title>
    <style>
    body{font-family:Georgia;background:#0a0a0a;color:#fff;margin:0;padding:20px}
    .header{text-align:center;padding:30px;background:linear-gradient(135deg,#1a001a,#0a000a);border-bottom:2px solid #ff69b4}
    h1{color:#ff69b4;font-size:40px}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px;max-width:1200px;margin:30px auto}
    .card{background:#1a1a1a;border:1px solid #333;padding:25px;border-radius:10px}
    .card h3{color:#ff69b4;margin-top:0}
    .btn{background:#ff69b4;color:#fff;padding:12px 25px;border:none;border-radius:5px;font-weight:bold;cursor:pointer;text-decoration:none;display:inline-block;margin:5px}
    input,select{width:100%;padding:10px;margin:5px 0;background:#0a0a0a;border:1px solid #333;color:#fff;border-radius:5px}
    </style></head><body>
    <div class="header"><h1>👨‍👩‍👧‍👦 FAMILY & HEIRS</h1><p>Build Your Dynasty</p></div>
    <div class="grid">
    <div class="card"><h3>💒 Marry</h3>
    <form action="/family/marry" method="post">
    <input name="person1" placeholder="Your username">
    <input name="person2" placeholder="Spouse username">
    <input name="prenup" placeholder="Prenup amount (0 for none)">
    <button type="submit" class="btn">Get Married 💒</button></form></div>
    
    <div class="card"><h3>👶 Have a Child</h3>
    <form action="/family/child" method="post">
    <input name="parent1" placeholder="Your username">
    <input name="parent2" placeholder="Spouse username">
    <input name="name" placeholder="Child's full name">
    <select name="gender"><option>Random</option><option>Male</option><option>Female</option></select>
    <button type="submit" class="btn">Welcome Baby 👶</button></form></div>
    
    <div class="card"><h3>🎓 Education</h3>
    <form action="/family/education" method="post">
    <input name="child" placeholder="Child's username">
    <select name="institution"><option>Harvard University ($250k)</option><option>Oxford University ($200k)</option><option>MIT ($220k)</option><option>Stanford ($240k)</option><option>Yale ($230k)</option></select>
    <button type="submit" class="btn">Send to School 🎓</button></form></div>
    
    <div class="card"><h3>⚰️ Process Inheritance</h3>
    <form action="/family/inheritance" method="post">
    <input name="deceased" placeholder="Deceased username">
    <button type="submit" class="btn" style="background:#666">Transfer Assets ⚰️</button></form></div>
    
    <div class="card"><h3>🌳 Family Tree</h3>
    <form action="/family/tree" method="get">
    <input name="user" placeholder="Username">
    <button type="submit" class="btn">View Tree 🌳</button></form></div>
    </div></body></html>"""

@app.route('/family/marry', methods=['POST'])
def family_marry():
    from flask import request
    result = family.marry(request.form.get("person1"), request.form.get("person2"),
                          float(request.form.get("prenup", 0)))
    return f"<h1>{'✅' if result['status']=='ok' else '❌'}</h1><p>{result.get('message')}</p><a href='/family'>Back</a>"

@app.route('/family/child', methods=['POST'])
def family_child():
    from flask import request
    gender = request.form.get("gender")
    if gender == "Random": gender = None
    result = family.have_child(request.form.get("parent1"), request.form.get("parent2"),
                                request.form.get("name"), gender)
    return f"<h1>{'✅' if result['status']=='ok' else '❌'}</h1><p>{result.get('message')}</p><a href='/family'>Back</a>"

@app.route('/family/education', methods=['POST'])
def family_education():
    from flask import request
    institution = request.form.get("institution")
    costs = {"Harvard University ($250k)": 250000, "Oxford University ($200k)": 200000,
             "MIT ($220k)": 220000, "Stanford ($240k)": 240000, "Yale ($230k)": 230000}
    cost = costs.get(institution, 200000)
    degree = institution.split(" (")[0]
    result = family.send_to_school(request.form.get("child"), degree.split(" University")[0] + " University", "Bachelor's", cost)
    return f"<h1>{'✅' if result['status']=='ok' else '❌'}</h1><p>{result.get('message')}</p><a href='/family'>Back</a>"

@app.route('/family/inheritance', methods=['POST'])
def family_inheritance():
    from flask import request
    result = family.process_inheritance(request.form.get("deceased"))
    return f"<h1>{'✅' if result['status']=='ok' else '❌'}</h1><p>{result.get('message')}</p><a href='/family'>Back</a>"

@app.route('/family/tree')
def family_tree():
    from flask import request
    user = request.args.get("user", "")
    tree = family.get_family_tree(user)
    if not tree:
        return "Character not found."
    char = tree["character"]
    html = f"<h1 style='color:#ff69b4'>🌳 Family Tree: {char['full_name']}</h1>"
    html += f"<p>Age: {char['age']} | Dynasty: {char['dynasty_name']} | Generation: {char['generation']}</p>"
    if tree["spouse"]:
        html += f"<h3>💒 Spouse: {tree['spouse']['full_name']}</h3>"
    if tree["children"]:
        html += "<h3>👶 Children:</h3>"
        for child in tree["children"]:
            html += f"<p>👤 {child['full_name']} ({child['gender']}) — Born {child['birth_year']}, Talent: {child['talent']}</p>"
    if tree["parents"]:
        html += "<h3>👴 Parents:</h3>"
        for parent in tree["parents"]:
            html += f"<p>{parent['full_name']}</p>"
    html += "<a href='/family'>Back</a>"
    return html

@app.route('/protect')
def protect_home():
    """Asset Protection Dashboard."""
    return """<!DOCTYPE html><html><head><title>Wyllene Asset Protection</title>
    <style>
    body{font-family:Georgia;background:#0a0a0a;color:#fff;margin:0;padding:20px}
    .header{text-align:center;padding:30px;background:linear-gradient(135deg,#1a0000,#0a0000);border-bottom:2px solid #ff4444}
    h1{color:#ff4444;font-size:40px}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px;max-width:1200px;margin:30px auto}
    .card{background:#1a1a1a;border:1px solid #333;padding:25px;border-radius:10px}
    .card h3{color:#ff4444;margin-top:0}
    .btn{background:#ff4444;color:#fff;padding:12px 25px;border:none;border-radius:5px;font-weight:bold;cursor:pointer;text-decoration:none;display:inline-block;margin:5px}
    input,select{width:100%;padding:10px;margin:5px 0;background:#0a0a0a;border:1px solid #333;color:#fff;border-radius:5px}
    </style></head><body>
    <div class="header"><h1>🛡️ ASSET PROTECTION</h1><p>Wealth Defense & Legal Shield</p></div>
    <div class="grid">
    <div class="card"><h3>🏢 Create LLC</h3>
    <form action="/protect/llc" method="post">
    <input name="owner" placeholder="Your username">
    <input name="company_name" placeholder="LLC Name">
    <select name="jurisdiction"><option>Delaware</option><option>Wyoming</option><option>Nevada</option><option>Cayman Islands</option></select>
    <input name="assets" placeholder="Assets to protect ($)">
    <button type="submit" class="btn">Form LLC</button></form></div>
    
    <div class="card"><h3>🏦 Offshore Trust</h3>
    <form action="/protect/offshore" method="post">
    <input name="creator" placeholder="Your username">
    <input name="trust_name" placeholder="Trust Name">
    <select name="jurisdiction"><option>Cayman Islands</option><option>Switzerland</option><option>Singapore</option><option>Liechtenstein</option><option>Dubai</option></select>
    <input name="amount" placeholder="Amount to transfer ($)">
    <button type="submit" class="btn">Create Trust</button></form></div>
    
    <div class="card"><h3>🛡️ Insurance</h3>
    <form action="/protect/insurance" method="post">
    <input name="username" placeholder="Your username">
    <select name="type"><option>Liability</option><option>Property</option><option>Life</option><option>Cyber</option><option>Directors & Officers</option></select>
    <input name="coverage" placeholder="Coverage amount ($)">
    <button type="submit" class="btn">Buy Insurance</button></form></div>
    
    <div class="card"><h3>📜 Estate Plan</h3>
    <form action="/protect/will" method="post">
    <input name="username" placeholder="Your username">
    <input name="executor" placeholder="Executor name">
    <input name="beneficiaries" placeholder="Beneficiaries (comma separated)">
    <button type="submit" class="btn">Create Will</button></form></div>
    
    <div class="card"><h3>💍 Pre-Nup</h3>
    <form action="/protect/prenup" method="post">
    <input name="person1" placeholder="Your username">
    <input name="person2" placeholder="Spouse username">
    <input name="assets" placeholder="Assets to protect ($)">
    <button type="submit" class="btn">Sign Pre-Nup</button></form></div>
    
    <div class="card"><h3>🏛️ Foundation</h3>
    <form action="/protect/foundation" method="post">
    <input name="founder" placeholder="Your username">
    <input name="name" placeholder="Foundation Name">
    <input name="amount" placeholder="Endowment ($)">
    <button type="submit" class="btn">Create Foundation</button></form></div>
    </div></body></html>"""

@app.route('/protect/llc', methods=['POST'])
def protect_llc():
    from flask import request
    result = protection.create_llc(request.form.get("owner"), request.form.get("company_name"),
                                    request.form.get("jurisdiction"), float(request.form.get("assets", 0)))
    return f"<h1>{'✅' if result['status']=='ok' else '❌'}</h1><p>{result.get('message')}</p><a href='/protect'>Back</a>"

@app.route('/protect/offshore', methods=['POST'])
def protect_offshore():
    from flask import request
    result = protection.create_offshore_trust(request.form.get("creator"), request.form.get("trust_name"),
                                               request.form.get("jurisdiction"), float(request.form.get("amount", 0)))
    return f"<h1>{'✅' if result['status']=='ok' else '❌'}</h1><p>{result.get('message')}</p><a href='/protect'>Back</a>"

@app.route('/protect/insurance', methods=['POST'])
def protect_insurance():
    from flask import request
    result = protection.buy_insurance(request.form.get("username"), request.form.get("type"),
                                       float(request.form.get("coverage", 0)))
    return f"<h1>{'✅' if result['status']=='ok' else '❌'}</h1><p>{result.get('message')}</p><a href='/protect'>Back</a>"

@app.route('/protect/will', methods=['POST'])
def protect_will():
    from flask import request
    result = protection.create_will(request.form.get("username"), request.form.get("executor"),
                                     request.form.get("beneficiaries"))
    return f"<h1>{'✅' if result['status']=='ok' else '❌'}</h1><p>{result.get('message')}</p><a href='/protect'>Back</a>"

@app.route('/protect/prenup', methods=['POST'])
def protect_prenup():
    from flask import request
    result = protection.sign_prenup(request.form.get("person1"), request.form.get("person2"),
                                     float(request.form.get("assets", 0)))
    return f"<h1>{'✅' if result['status']=='ok' else '❌'}</h1><p>{result.get('message')}</p><a href='/protect'>Back</a>"

@app.route('/protect/foundation', methods=['POST'])
def protect_foundation():
    from flask import request
    result = protection.create_foundation(request.form.get("founder"), request.form.get("name"),
                                           float(request.form.get("amount", 0)))
    return f"<h1>{'✅' if result['status']=='ok' else '❌'}</h1><p>{result.get('message')}</p><a href='/protect'>Back</a>"

@app.route('/dynasty')
def dynasty_home():
    """Dynasty — Generational Wealth Simulator."""
    return """<!DOCTYPE html><html><head><title>Wyllene Dynasty</title>
    <style>
    body{font-family:Georgia;background:#0a0a0a;color:#fff;margin:0;padding:20px}
    .header{text-align:center;padding:40px;background:linear-gradient(135deg,#1a1a00,#0a0a00);border-bottom:3px solid gold}
    h1{color:gold;font-size:48px;letter-spacing:5px}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px;max-width:1200px;margin:30px auto}
    .card{background:#1a1a1a;border:1px solid #333;padding:25px;border-radius:10px}
    .card h3{color:gold;margin-top:0}
    .btn{background:gold;color:#0a0a0a;padding:12px 25px;border:none;border-radius:5px;font-weight:bold;cursor:pointer;text-decoration:none;display:inline-block;margin:5px}
    input,select{width:100%;padding:10px;margin:5px 0;background:#0a0a0a;border:1px solid #333;color:#fff;border-radius:5px}
    .stat{font-size:28px;color:gold;font-weight:bold}
    </style></head><body>
    <div class="header"><h1>🏰 WYLLENE DYNASTY</h1><p>Generational Wealth Engine</p></div>
    <div class="grid">
    <div class="card"><h3>Create Character</h3>
    <form action="/dynasty/create" method="post">
    <input name="username" placeholder="Username" required>
    <input name="full_name" placeholder="Full Name" required>
    <input name="age" placeholder="Age (default 18)" value="18">
    <select name="education"><option>High School</option><option>Bachelor's</option><option>Master's</option><option>PhD</option></select>
    <select name="career"><option>Unemployed</option><option>Entry Level</option><option>Professional</option><option>Manager</option><option>Entrepreneur</option></select>
    <input name="starting_wealth" placeholder="Starting Wealth ($)" value="10000">
    <input name="dynasty_name" placeholder="Dynasty Name (e.g., Vanderbilt)">
    <button type="submit" class="btn">Start Life</button></form></div>
    <div class="card"><h3>View Profile</h3>
    <form action="/dynasty/profile" method="get">
    <input name="user" placeholder="Username"><button type="submit" class="btn">View</button></form></div>
    <div class="card"><h3>Advance Year</h3>
    <form action="/dynasty/advance" method="post">
    <input name="username" placeholder="Username"><button type="submit" class="btn">Advance One Year →</button></form></div>
    <div class="card"><h3>Start Business</h3>
    <form action="/dynasty/business" method="post">
    <input name="owner" placeholder="Your username">
    <input name="name" placeholder="Business name">
    <input name="sector" placeholder="Sector (Tech, Finance, etc.)">
    <input name="investment" placeholder="Investment amount ($)">
    <button type="submit" class="btn">Launch Business</button></form></div>
    <div class="card"><h3>Create Trust Fund</h3>
    <form action="/dynasty/trust" method="post">
    <input name="creator" placeholder="Your username">
    <input name="beneficiary" placeholder="Beneficiary username">
    <input name="amount" placeholder="Amount ($)">
    <input name="unlock_age" placeholder="Unlock age (default 25)" value="25">
    <button type="submit" class="btn">Create Trust Fund</button></form></div>
    </div></body></html>"""

@app.route('/dynasty/create', methods=['POST'])
def dynasty_create():
    from flask import request
    result = dynasty.create_character(
        request.form.get("username"), request.form.get("full_name"),
        int(request.form.get("age", 18)), request.form.get("education", "High School"),
        float(request.form.get("starting_wealth", 10000)),
        request.form.get("dynasty_name", "")
    )
    return f"<h1>{'✅ Created!' if result['status']=='ok' else '❌ Error'}</h1><p>{result}</p><a href='/dynasty'>Back</a>"

@app.route('/dynasty/profile')
def dynasty_profile():
    from flask import request
    user = request.args.get("user", "")
    char = dynasty.get_character(user)
    if not char: return "Character not found."
    html = f"<h1 style='color:gold'>👤 {char['full_name']}</h1>"
    html += f"<p>Age: {char['age']} | Education: {char['education']} | Career: {char['career']}</p>"
    html += f"<p>Net Worth: ${char.get('total_assets',0):,.2f}</p>"
    html += f"<p>Dynasty: {char['dynasty_name']} | Generation: {char['generation']}</p>"
    if char.get("children"):
        html += "<h3>Children</h3>"
        for child in char["children"]:
            html += f"<p>👶 {child['full_name']} (Age {child['age']})</p>"
    html += "<a href='/dynasty'>Back</a>"
    return html

@app.route('/dynasty/advance', methods=['POST'])
def dynasty_advance():
    from flask import request
    result = dynasty.advance_year(request.form.get("username"))
    return f"<h1>⏩ Year Advanced!</h1><p>Age: {result.get('new_age')}</p><p>Net Change: ${result.get('net_change',0):,.2f}</p><a href='/dynasty'>Back</a>"

@app.route('/dynasty/business', methods=['POST'])
def dynasty_business():
    from flask import request
    result = dynasty.start_business(
        request.form.get("owner"), request.form.get("name"),
        request.form.get("sector"), float(request.form.get("investment", 0))
    )
    return f"<h1>{'✅' if result['status']=='ok' else '❌'}</h1><p>{result.get('message')}</p><a href='/dynasty'>Back</a>"

@app.route('/dynasty/trust', methods=['POST'])
def dynasty_trust():
    from flask import request
    result = dynasty.create_trust_fund(
        request.form.get("creator"), request.form.get("beneficiary"),
        float(request.form.get("amount", 0)), int(request.form.get("unlock_age", 25))
    )
    return f"<h1>{'✅' if result['status']=='ok' else '❌'}</h1><p>{result.get('message')}</p><a href='/dynasty'>Back</a>"

@app.route('/wealth')
def wealth_home():
    """Private Wealth homepage."""
    return """<!DOCTYPE html><html><head><title>Wyllene Private Wealth</title>
    <style>body{font-family:Georgia;background:#0a0a0a;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;text-align:center}
    .box{border:2px solid #D4AF37;padding:60px;border-radius:10px;background:#1a1a1a}
    h1{color:#D4AF37;font-size:48px;letter-spacing:5px}
    p{color:#aaa;font-size:18px;margin:20px 0}
    input{padding:15px 30px;font-size:18px;background:#0a0a0a;border:1px solid #D4AF37;color:#fff;border-radius:5px;text-align:center}
    button{padding:15px 40px;background:#D4AF37;color:#0a0a0a;border:none;border-radius:5px;font-weight:bold;font-size:18px;cursor:pointer;margin-left:10px}
    </style></head><body><div class="box">
    <h1>👑 WYLLENE PRIVATE WEALTH</h1>
    <p>Exclusive banking for the elite</p>
    <form action="/wealth/login" method="post">
    <input name="invite_code" placeholder="Enter invitation code">
    <button type="submit">Enter</button>
    </form></div></body></html>"""

@app.route('/wealth/login', methods=['POST'])
def wealth_login():
    """Verify invitation code."""
    from flask import request
    code = request.form.get("invite_code", "").strip().upper()
    from wealth_config import VALID_INVITE_CODES
    if code in VALID_INVITE_CODES:
        return f"""<html><head><title>Register</title>
        <style>body{{font-family:Georgia;background:#0a0a0a;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh}}
        .box{{border:2px solid #D4AF37;padding:40px;border-radius:10px;background:#1a1a1a}}
        input{{display:block;width:100%;padding:12px;margin:10px 0;background:#0a0a0a;border:1px solid #D4AF37;color:#fff;border-radius:5px}}
        button{{background:#D4AF37;color:#0a0a0a;padding:12px 30px;border:none;border-radius:5px;font-weight:bold;cursor:pointer}}
        </style></head><body><div class="box">
        <h2 style="color:#D4AF37;">Register for Private Wealth</h2>
        <form action="/wealth/register" method="post">
        <input type="hidden" name="invite_code" value="{code}">
        <input name="username" placeholder="Choose username" required>
        <input name="pin" placeholder="Create PIN" type="password" required>
        <input name="full_name" placeholder="Full name" required>
        <button type="submit">Join</button>
        </form></div></body></html>"""
    return "Invalid invitation code. <a href='/wealth'>Try again</a>"

@app.route('/wealth/register', methods=['POST'])
def wealth_register():
    """Register new wealth client."""
    from flask import request
    username = request.form.get("username", "")
    pin = request.form.get("pin", "")
    full_name = request.form.get("full_name", "")
    invite_code = request.form.get("invite_code", "")
    
    from wealth_db import add_client, get_client, get_assets, get_net_worth, update_tier
    from wealth_config import TIERS, SERVICES
    result = add_client(username, pin, full_name, invite_code)
    if result["status"] == "ok":
        return f"Welcome to Wyllene Private Wealth, {full_name}! Your personal banker is {result['banker']}. <a href='/wealth/me?user={username}'>View Dashboard</a>"
    return f"Error: {result.get('message','')} <a href='/wealth'>Back</a>"

@app.route('/wealth/jets')
def jets_page():
    from luxury import JETS
    html = '<h1 style="color:#D4AF37">🛩️ Private Jet Fleet</h1>'
    for j in JETS:
        html += f'<div style="background:#1a1a1a;padding:20px;margin:10px;border-radius:10px;border:1px solid #333">'
        html += f'<h3>{j["image"]} {j["name"]}</h3>'
        html += f'<p>Range: {j["range"]} | Seats: {j["seats"]} | ${j["price_per_hour"]:,}/hour</p>'
        html += f'</div>'
    return html

@app.route('/wealth/cars')
def cars_page():
    from luxury import CARS
    html = '<h1 style="color:#D4AF37">🏎️ Luxury Car Fleet</h1>'
    for c in CARS:
        html += f'<div style="background:#1a1a1a;padding:20px;margin:10px;border-radius:10px;border:1px solid #333">'
        html += f'<h3>{c["image"]} {c["name"]}</h3>'
        html += f'<p>Price: ${c["price"]:,} | Top Speed: {c["speed"]}</p>'
        html += f'</div>'
    return html

@app.route('/wealth/hotels')
def hotels_page():
    from luxury import HOTELS
    html = '<h1 style="color:#D4AF37">🏨 Five-Star Hotels</h1>'
    for h in HOTELS:
        html += f'<div style="background:#1a1a1a;padding:20px;margin:10px;border-radius:10px;border:1px solid #333">'
        html += f'<h3>{h["image"]} {h["name"]} — {h["location"]}</h3>'
        html += f'<p>${h["price_per_night"]:,}/night | {"⭐" * h["rating"]}</p>'
        html += f'</div>'
    return html

@app.route('/wealth/wines')
def wines_page():
    from luxury import WINES
    html = '<h1 style="color:#D4AF37">🍷 Fine Wine Collection</h1>'
    for w in WINES:
        html += f'<div style="background:#1a1a1a;padding:20px;margin:10px;border-radius:10px;border:1px solid #333">'
        html += f'<h3>{w["image"]} {w["name"]} ({w["vintage"]})</h3>'
        html += f'<p>{w["region"]} | ${w["price"]:,}</p>'
        html += f'</div>'
    return html

@app.route('/wealth/yachts')
def yachts_page():
    from luxury import YACHTS
    html = '<h1 style="color:#D4AF37">🛥️ Yacht Charter</h1>'
    for y in YACHTS:
        html += f'<div style="background:#1a1a1a;padding:20px;margin:10px;border-radius:10px;border:1px solid #333">'
        html += f'<h3>{y["image"]} {y["name"]}</h3>'
        html += f'<p>{y["length"]} | {y["guests"]} guests | ${y["price_per_week"]:,}/week</p>'
        html += f'</div>'
    return html

@app.route('/wealth/jewelry')
def jewelry_page():
    from luxury import JEWELRY
    html = '<h1 style="color:#D4AF37">💎 Jewelry Collection</h1>'
    for j in JEWELRY:
        html += f'<div style="background:#1a1a1a;padding:20px;margin:10px;border-radius:10px;border:1px solid #333">'
        html += f'<h3>{j["image"]} {j["name"]}</h3>'
        html += f'<p>{j["carats"]} carats | ${j["price"]:,}</p>'
        html += f'</div>'
    return html

@app.route('/wealth/events')
def events_page():
    from luxury import EVENTS
    html = '<h1 style="color:#D4AF37">🎫 Exclusive Events</h1>'
    for e in EVENTS:
        html += f'<div style="background:#1a1a1a;padding:20px;margin:10px;border-radius:10px;border:1px solid #333">'
        html += f'<h3>{e["image"]} {e["name"]}</h3>'
        html += f'<p>{e["location"]} | {e["date"]} | ${e["price"]:,}</p>'
        html += f'</div>'
    return html

@app.route('/wealth/me')
def wealth_dashboard():
    """Client wealth dashboard."""
    from flask import request, render_template_string
    username = request.args.get("user", "")
    from wealth_db import get_client, get_assets, get_net_worth, update_tier
    from wealth_config import TIERS, SERVICES
    client = get_client(username)
    if not client:
        return "Client not found."
    
    assets = get_assets(username)
    net_worth = get_net_worth(username)
    tier = update_tier(username)
    benefits = TIERS.get(tier, {}).get("benefits", [])
    
    with open("templates/wealth.html") as f:
        template = f.read()
    
    return render_template_string(
        template,
        banker=client["banker_name"],
        net_worth=net_worth,
        tier=tier,
        benefits=benefits,
        assets=assets,
        services=SERVICES
    )

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
