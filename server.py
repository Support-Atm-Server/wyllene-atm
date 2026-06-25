"""Wyllene Dynasty — Clean Server (No Duplicates)."""
import os, json, socket, threading, time, secrets
from flask import Flask, request, jsonify, send_from_directory
from config import HOST, SOCKET_PORT, WEB_PORT, APPROVAL_THRESHOLD
from database import *
from fraud_detector import detector
from currency import currency_mgr, FIAT_CURRENCIES, CRYPTO_CURRENCIES
from analytics import analytics
from wealth_db import *
from wealth_config import *
from dynasty_engine import dynasty
from asset_protection import protection
from family_legacy import family
import market_economy
from advanced_features import advanced
from dna_legacy import dna

app = Flask(__name__)

# ============================================================
# DASHBOARD
# ============================================================
@app.route('/dashboard')
def unified_dashboard():
    economy = market_economy.economy
    market = economy.generate_market_year()
    stocks = economy.get_stock_prices()
    leaderboard = economy.update_leaderboard()
    total_dynasties = len(leaderboard)
    total_wealth = sum(d['wealth'] for d in leaderboard)
    total_members = sum(d['members'] for d in leaderboard)
    
    html = """<!DOCTYPE html><html><head><title>Wyllene Dynasty</title>
    <style>body{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px}
    h1{color:#D4AF37}h2{color:#D4AF37;margin-top:30px}
    table{border-collapse:collapse;width:100%;max-width:800px;margin:10px 0}
    th,td{border:1px solid #222;padding:12px}th{background:#0a0a15;color:#D4AF37}
    a{color:#D4AF37;text-decoration:none;margin:0 10px}
    .card{background:#0d0d20;border:1px solid #222;padding:20px;margin:15px 0;border-radius:10px}
    </style></head><body>
    <h1>🏰 WYLLENE DYNASTY COMMAND CENTER</h1>
    <p style='color:#888'>Founded by <b style='color:#D4AF37'>Lunga Titus Malebadi</b> — Founder & CEO</p>
    <div class='card'><p>Dynasties: <b>""" + str(total_dynasties) + """</b> | Wealth: <b style='color:#D4AF37'>$""" + f"{total_wealth:,.0f}" + """</b> | Members: <b>""" + str(total_members) + """</b> | Stocks: <b>""" + str(len(stocks)) + """</b></p></div>
    <h2>🏆 Dynasty Leaderboard</h2><table><tr><th>Rank</th><th>Dynasty</th><th>Wealth</th><th>Score</th></tr>"""
    
    for i, d in enumerate(leaderboard[:10]):
        medals = {0:'🥇',1:'🥈',2:'🥉'}
        rank = medals.get(i, str(i+1))
        html += f"<tr><td>{rank}</td><td>{d['dynasty']}</td><td style='color:#D4AF37'>${d['wealth']:,.0f}</td><td>{d['score']:,}</td></tr>"
    html += "</table>"
    html += "<p><a href='/dynasty'>Life</a> | <a href='/market'>Markets</a> | <a href='/protect'>Protection</a> | <a href='/family'>Family</a> | <a href='/wealth'>Wealth</a> | <a href='/chat'>AI</a></p>"
    html += "</body></html>"
    return html

# ============================================================
# MARKETS
# ============================================================
@app.route('/market')
def market_home():
    economy = market_economy.economy
    market = economy.generate_market_year()
    stocks = economy.get_stock_prices()
    leaderboard = economy.update_leaderboard()
    
    html = """<!DOCTYPE html><html><head><title>Wyllene Markets</title>
    <style>body{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px}
    h1{color:#00ff00}h2{color:#00ff00;margin-top:30px}
    table{border-collapse:collapse;width:100%;max-width:800px;margin:10px 0}
    th,td{border:1px solid #222;padding:12px}th{background:#0a0a15;color:#00ff00}
    a{color:#00ff00;text-decoration:none;margin:0 10px}
    .card{background:#0d0d20;border:1px solid #222;padding:20px;margin:15px 0;border-radius:10px}
    .up{color:#4CAF50}.down{color:#F44336}
    </style></head><body>
    <h1>📈 WYLLENE MARKETS</h1>
    <div class='card'><p>Market: <b>""" + market['market'] + """</b> | Growth: <b class='""" + ('up' if market['growth']>0 else 'down') + """'>""" + f"{market['growth']*100:+.1f}%" + """</b> | Volatility: <b>""" + market['volatility'] + """</b></p></div>
    <h2>Stock Prices</h2><table><tr><th>Ticker</th><th>Company</th><th>Price</th><th>Sector</th></tr>"""
    
    for s in stocks:
        color = "up" if s['price'] > 100 else "down"
        html += f"<tr><td><b>{s['ticker']}</b></td><td>{s['name']}</td><td class='{color}'>${s['price']:.2f}</td><td>{s['sector']}</td></tr>"
    html += "</table>"
    html += "<h2>Leaderboard</h2><table><tr><th>Rank</th><th>Dynasty</th><th>Wealth</th><th>Score</th></tr>"
    for i, d in enumerate(leaderboard[:10]):
        html += f"<tr><td>{i+1}</td><td>{d['dynasty']}</td><td style='color:#D4AF37'>${d['wealth']:,.0f}</td><td>{d['score']:,}</td></tr>"
    html += "</table>"
    html += "<p><a href='/market/ipo'>🚀 IPO</a> | <a href='/dashboard'>Dashboard</a></p>"
    html += "</body></html>"
    return html

@app.route('/market/ipo', methods=['GET','POST'])
def market_ipo():
    economy = market_economy.economy
    if request.method == 'GET':
        return """<!DOCTYPE html><html><head><title>IPO</title>
        <style>body{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px}
        h1{color:#00ff00}input,select{display:block;width:300px;padding:10px;margin:10px 0;background:#0d0d20;border:1px solid #333;color:#fff}
        button{background:#00ff00;color:#000;padding:12px 30px;border:none;cursor:pointer;font-weight:bold}</style></head><body>
        <h1>🚀 IPO Your Company</h1>
        <form method='post'>
        <input name='founder' placeholder='Your username' required>
        <input name='business' placeholder='Business name' required>
        <input name='ticker' placeholder='Ticker (e.g., AAPL)' required>
        <select name='sector'><option>Tech</option><option>Finance</option><option>Healthcare</option><option>Energy</option></select>
        <input name='price' placeholder='Share price ($)' required>
        <input name='shares' placeholder='Total shares' required>
        <button type='submit'>Go Public! 🚀</button></form></body></html>"""
    
    result = economy.ipo_company(
        request.form.get("founder"), request.form.get("business"),
        request.form.get("ticker"), request.form.get("sector"),
        float(request.form.get("price", 0)), int(request.form.get("shares", 0))
    )
    if result["status"] == "ok":
        return f"<h1 style='color:gold'>✅ Success!</h1><p>{result['message']}</p><a href='/market'>Back</a>"
    return f"<h1 style='color:red'>❌ Error</h1><p>{result.get('message')}</p><a href='/market'>Back</a>"

# ============================================================
# MAIN SERVER STARTUP
# ============================================================


# ============================================================
# S-TIER EXCLUSIVE FEATURES
# ============================================================
@app.route('/exclusive')
def exclusive_hub():
    """S-Tier Exclusive Features Hub."""
    html = """<!DOCTYPE html><html><head><title>Wyllene Elite Features</title>
    <style>
    body{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px}
    h1{color:#D4AF37;text-align:center;font-size:36px}
    .subtitle{text-align:center;color:#888;font-style:italic;margin-bottom:30px}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(350px,1fr));gap:25px;max-width:1200px;margin:0 auto}
    .card{background:#0d0d20;border:1px solid #222;border-radius:12px;padding:25px;transition:all 0.3s}
    .card:hover{border-color:#D4AF37;transform:translateY(-3px)}
    .card h3{color:#D4AF37;font-size:20px;margin-bottom:15px}
    .card p{color:#aaa;margin:10px 0}
    .btn{display:inline-block;padding:10px 20px;border-radius:5px;text-decoration:none;font-weight:bold;margin:5px;cursor:pointer}
    .btn-gold{background:#D4AF37;color:#000}
    .btn-outline{border:1px solid #D4AF37;color:#D4AF37;background:transparent}
    .btn-red{border:1px solid #ff4444;color:#ff4444;background:transparent}
    .btn-blue{border:1px solid #4444ff;color:#4444ff;background:transparent}
    .btn-green{border:1px solid #44ff44;color:#44ff44;background:transparent}
    .icon{font-size:36px}
    .coming-soon{opacity:0.5;pointer-events:none}
    </style></head><body>
    <h1>👑 S-TIER EXCLUSIVE FEATURES</h1>
    <p class="subtitle">Features no other platform has — Built by Lunga Titus Malebadi</p>
    
    <div class="grid">
        <div class="card">
            <div class="icon">💀</div>
            <h3>Black Swan Events</h3>
            <p>Unpredictable global events that reshape the economy.</p>
            <a href="/exclusive/blackswan" class="btn btn-red">Trigger Event</a>
        </div>
        <div class="card">
            <div class="icon">🏛️</div>
            <h3>Political Office</h3>
            <p>Run for government. Change laws. Control tax rates.</p>
            <a href="/exclusive/politics" class="btn btn-blue">Run for Office</a>
        </div>
        <div class="card">
            <div class="icon">🚀</div>
            <h3>Space Economy</h3>
            <p>Invest in asteroid mining, Mars colonies, orbital hotels.</p>
            <a href="/exclusive/space" class="btn btn-outline">Explore Space</a>
        </div>
        <div class="card">
            <div class="icon">🎨</div>
            <h3>Art & Culture</h3>
            <p>Commission masterpieces. Build museums. Shape culture.</p>
            <a href="/exclusive/art" class="btn btn-gold">Patron Arts</a>
        </div>
        <div class="card">
            <div class="icon">⚔️</div>
            <h3>Succession Wars</h3>
            <p>Heirs battle for dynasty control. Drama. Betrayal. Victory.</p>
            <a href="/exclusive/succession" class="btn btn-red">Start War</a>
        </div>
        <div class="card coming-soon">
            <div class="icon">🧬</div>
            <h3>DNA Legacy (Coming Soon)</h3>
            <p>Pass traits, talents, and genius to your bloodline.</p>
        </div>
        <div class="card coming-soon">
            <div class="icon">🌍</div>
            <h3>Geopolitical Influence (Coming Soon)</h3>
            <p>Your dynasty shapes world events in real-time.</p>
        </div>
        <div class="card coming-soon">
            <div class="icon">🕰️</div>
            <h3>Time Travel (Coming Soon)</h3>
            <p>Replay historical markets with your dynasty.</p>
        </div>
    </div>
    <p style="text-align:center;margin-top:30px"><a href='/dashboard' style='color:#D4AF37'>Back to Command Center</a></p>
    </body></html>"""
    return html

@app.route('/exclusive/blackswan')
def blackswan_event():
    event = advanced.trigger_black_swan()
    html = f"""<!DOCTYPE html><html><head><title>Black Swan</title>
    <style>body{{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px;text-align:center}}
    h1{{color:#ff4444;font-size:48px}}p{{font-size:18px;margin:20px}}
    .impact{{font-size:60px;font-weight:bold;color:#ff4444}}
    a{{color:#D4AF37;text-decoration:none}}</style></head><body>
    <h1>💀 BLACK SWAN EVENT</h1>
    <h2>{event['name']}</h2>
    <p>{event['desc']}</p>
    <div class='impact'>{event['market_impact']*100:+.0f}%</div>
    <p>Market Impact</p>
    <a href='/exclusive'>Back</a></body></html>"""
    return html

@app.route('/exclusive/politics')
def politics():
    result = advanced.run_for_office()
    html = f"""<!DOCTYPE html><html><head><title>Politics</title>
    <style>body{{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px;text-align:center}}
    h1{{color:#4444ff}}p{{font-size:18px}}
    a{{color:#D4AF37}}</style></head><body>
    <h1>🏛️ POLITICAL AMBITION</h1>
    <h2>{result['office']}</h2>
    <p>{result['message']}</p>
    <a href='/exclusive'>Back</a></body></html>"""
    return html

@app.route('/exclusive/space')
def space_investment():
    result = advanced.invest_space()
    html = f"""<!DOCTYPE html><html><head><title>Space Economy</title>
    <style>body{{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px;text-align:center}}
    h1{{color:#D4AF37}}p{{font-size:18px}}
    a{{color:#D4AF37}}</style></head><body>
    <h1>🚀 SPACE ECONOMY</h1>
    <h2>{result['name']}</h2>
    <p>Investment: ${result['cost']:,}</p>
    <p>Projected Return: {result['projected_return']}</p>
    <a href='/exclusive'>Back</a></body></html>"""
    return html

@app.route('/exclusive/art')
def art_patronage():
    result = advanced.patron_art()
    html = f"""<!DOCTYPE html><html><head><title>Art Patronage</title>
    <style>body{{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px;text-align:center}}
    h1{{color:#D4AF37}}p{{font-size:18px}}
    a{{color:#D4AF37}}</style></head><body>
    <h1>🎨 ART & CULTURE</h1>
    <h2>{result['name']}</h2>
    <p>{result['message']}</p>
    <a href='/exclusive'>Back</a></body></html>"""
    return html


@app.route('/dna')
def dna_hub():
    """DNA Legacy Hub."""
    bloodlines = dna.get_all_bloodlines()
    
    html = """<!DOCTYPE html><html><head><title>Wyllene DNA Legacy</title>
    <style>
    body{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px}
    h1{color:#D4AF37;text-align:center;font-size:36px}
    .subtitle{text-align:center;color:#888;font-style:italic}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:25px;max-width:1200px;margin:30px auto}
    .card{background:#0d0d20;border:1px solid #222;border-radius:12px;padding:25px}
    .card h3{color:#D4AF37;margin-bottom:15px}
    table{width:100%;border-collapse:collapse;margin:10px 0}
    th,td{border:1px solid #222;padding:10px}
    th{background:#0a0a15;color:#D4AF37}
    .stat{display:inline-block;width:80px;text-align:center;margin:5px}
    .stat-value{font-size:24px;color:#D4AF37;font-weight:bold}
    .stat-label{font-size:10px;color:#888;text-transform:uppercase}
    .bar{background:#1a1a30;height:10px;border-radius:5px;margin:5px 0}
    .bar-fill{background:linear-gradient(90deg,#D4AF37,#F4D03F);height:100%;border-radius:5px}
    .talent-genius{color:#FFD700}.talent-prodigy{color:#00FFFF}.talent-savant{color:#FF00FF}
    .talent-gifted{color:#00FF00}.talent-normal{color:#AAA}
    .mutation{color:#FF4444;font-weight:bold}
    a{color:#D4AF37;text-decoration:none;margin:0 10px}
    </style></head><body>
    <h1>🧬 DNA LEGACY SYSTEM</h1>
    <p class="subtitle">Bloodlines. Traits. Mutations. Legacy.</p>
    
    <div class="grid">
        <div class="card">
            <h3>🩸 Bloodlines</h3>
            <table><tr><th>Bloodline</th><th>Founder</th><th>Members</th><th>Avg IQ</th></tr>"""
    
    for b in bloodlines[:5]:
        html += f"<tr><td><b>{b['name']}</b></td><td>{b['founder']}</td><td>{b.get('total_members',1)}</td><td>{b.get('avg_intelligence',50):.0f}</td></tr>"
    
    html += """</table></div>
        <div class="card">
            <h3>🧬 Generate DNA</h3>
            <p>Create a DNA profile for your character.</p>
            <form action='/dna/generate' method='post'>
            <input name='username' placeholder='Username' style='width:100%;padding:10px;margin:10px 0;background:#0a0a0a;border:1px solid #333;color:#fff'>
            <input name='bloodline' placeholder='Bloodline name (optional)' style='width:100%;padding:10px;margin:10px 0;background:#0a0a0a;border:1px solid #333;color:#fff'>
            <button type='submit' style='background:#D4AF37;color:#000;padding:10px 25px;border:none;cursor:pointer;font-weight:bold'>Generate DNA</button></form>
        </div>
        <div class="card">
            <h3>🔍 View DNA</h3>
            <form action='/dna/view' method='get'>
            <input name='username' placeholder='Username' style='width:100%;padding:10px;margin:10px 0;background:#0a0a0a;border:1px solid #333;color:#fff'>
            <button type='submit' style='background:#D4AF37;color:#000;padding:10px 25px;border:none;cursor:pointer;font-weight:bold'>View Profile</button></form>
        </div>
    </div>
    <p style='text-align:center'><a href='/dashboard'>Command Center</a> | <a href='/exclusive'>S-Tier Features</a></p>
    </body></html>"""
    return html

@app.route('/dna/generate', methods=['POST'])
def dna_generate():
    from flask import request
    username = request.form.get("username")
    bloodline = request.form.get("bloodline") or None
    result = dna.generate_dna(username, bloodline)
    
    html = f"""<!DOCTYPE html><html><head><title>DNA Generated</title>
    <style>body{{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px;text-align:center}}
    h1{{color:#D4AF37}}.card{{background:#0d0d20;border:1px solid #222;padding:30px;max-width:500px;margin:30px auto;border-radius:12px}}
    .stat{{display:inline-block;width:100px;margin:10px}}.stat-value{{font-size:28px;color:#D4AF37;font-weight:bold}}
    .stat-label{{font-size:10px;color:#888}}.talent{{font-size:24px;margin:20px 0}}
    .bar{{background:#1a1a30;height:8px;width:200px;margin:5px auto;border-radius:5px}}
    .bar-fill{{background:linear-gradient(90deg,#D4AF37,#F4D03F);height:100%;border-radius:5px}}
    .mutation{{color:#FF4444;font-weight:bold;margin:15px 0}}
    a{{color:#D4AF37}}</style></head><body>
    <h1>🧬 DNA PROFILE GENERATED</h1>
    <div class='card'>
    <h2>{username}</h2>
    <p>Bloodline: <b>{result['bloodline']}</b></p>
    <div class='stat'><div class='stat-value'>{result['intelligence']}</div><div class='stat-label'>Intelligence</div><div class='bar'><div class='bar-fill' style='width:{result['intelligence']}%'></div></div></div>
    <div class='stat'><div class='stat-value'>{result['charisma']}</div><div class='stat-label'>Charisma</div><div class='bar'><div class='bar-fill' style='width:{result['charisma']}%'></div></div></div>
    <div class='stat'><div class='stat-value'>{result['business_acumen']}</div><div class='stat-label'>Business</div><div class='bar'><div class='bar-fill' style='width:{result['business_acumen']}%'></div></div></div>
    <div class='stat'><div class='stat-value'>{result['risk_tolerance']}</div><div class='stat-label'>Risk</div><div class='bar'><div class='bar-fill' style='width:{result['risk_tolerance']}%'></div></div></div>
    <div class='stat'><div class='stat-value'>{result['longevity']}</div><div class='stat-label'>Longevity</div><div class='bar'><div class='bar-fill' style='width:{result['longevity']}%'></div></div></div>
    <div class='talent'>Talent: <b>{result['talent']}</b></div>"""
    
    if result['mutated']:
        html += f"<div class='mutation'>🧬 MUTATION: {result['mutation']}!</div>"
    
    html += """</div><a href='/dna'>Back</a></body></html>"""
    return html

@app.route('/dna/view')
def dna_view():
    from flask import request
    username = request.args.get("username")
    profile = dna.get_dna(username)
    if not profile:
        return "<h1>Not found</h1><a href='/dna'>Back</a>"
    
    html = f"""<!DOCTYPE html><html><head><title>{username} DNA</title>
    <style>body{{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px;text-align:center}}
    h1{{color:#D4AF37}}.card{{background:#0d0d20;border:1px solid #222;padding:30px;max-width:500px;margin:30px auto;border-radius:12px}}
    .stat{{display:inline-block;width:100px;margin:10px}}.stat-value{{font-size:28px;color:#D4AF37;font-weight:bold}}
    .stat-label{{font-size:10px;color:#888}}
    .bar{{background:#1a1a30;height:8px;width:200px;margin:5px auto;border-radius:5px}}
    .bar-fill{{background:linear-gradient(90deg,#D4AF37,#F4D03F);height:100%;border-radius:5px}}
    .mutation{{color:#FF4444}}a{{color:#D4AF37}}</style></head><body>
    <h1>🧬 {username}'s DNA</h1>
    <div class='card'>
    <p>Bloodline: <b>{profile['bloodline']}</b></p>
    <p>Talent: <b>{profile['talent']}</b></p>
    <p>Generation: {profile['generation']}</p>"""
    
    for trait in ['intelligence','charisma','business_acumen','risk_tolerance','longevity']:
        val = profile[trait]
        html += f"<div class='stat'><div class='stat-value'>{val}</div><div class='stat-label'>{trait.replace('_',' ').title()}</div><div class='bar'><div class='bar-fill' style='width:{val}%'></div></div></div>"
    
    if profile['mutated']:
        html += "<p class='mutation'>🧬 This character has a genetic mutation!</p>"
    
    html += "</div><a href='/dna'>Back</a></body></html>"
    return html

@app.route('/exclusive/succession')
def succession_war():
    heirs = ["Alexander", "Victoria", "Sebastian", "Isabella"]
    result = advanced.succession_war(heirs)
    html = f"""<!DOCTYPE html><html><head><title>Succession War</title>
    <style>body{{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px;text-align:center}}
    h1{{color:#ff4444}}p{{font-size:18px}}
    a{{color:#D4AF37}}</style></head><body>
    <h1>⚔️ SUCCESSION WAR</h1>
    <h2>Winner: {result.get('winner','Unknown')}</h2>
    <p>{result.get('message','')}</p>
    <p><i>{result.get('drama','')}</i></p>
    <a href='/exclusive'>Back</a></body></html>"""
    return html

# ============================================================
# SOCKET SERVER
# ============================================================
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
                    resp = {"status":"ok","role":user["role"],"balance":user["balance"]}
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
                    resp = {"status":"ok","new_balance":user["balance"]}
            elif cmd == "WITHDRAW":
                amt = float(req.get("amount",0))
                user = get_user(username)
                if amt <= 0 or amt > user["balance"]: resp = {"status":"error","message":"Insufficient funds"}
                else:
                    user["balance"] -= amt; update_user(username, user)
                    add_transaction(username, "WITHDRAW", amt)
                    resp = {"status":"ok","new_balance":user["balance"]}
            elif cmd == "SET_CHAT_ID":
                user = get_user(username)
                if user: user["chat_id"] = req.get("chat_id",""); update_user(username, user)
                resp = {"status":"ok"}
            else: resp = {"status":"error","message":"Unknown command"}
            
            conn.sendall(json.dumps(resp).encode())
    except: pass
    finally: conn.close()

def start_socket():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, SOCKET_PORT))
    server.listen(5)
    print(f"🔌 Socket server on port {SOCKET_PORT}")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    print("🏰 Wyllene Dynasty Starting...")
    initialize()
    threading.Thread(target=start_socket, daemon=True).start()
    app.run(host="0.0.0.0", port=WEB_PORT)
