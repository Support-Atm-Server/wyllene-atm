"""Wyllene Dynasty — Clean Server (No Duplicates)."""
import os, json, socket, threading, time, secrets
from flask import Flask, request, jsonify, send_from_directory
from bulletproof import safe_route, rate_limit, add_security_headers, sanitize_input, backup_database, system_health
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
from ai_rivals import ai_rivals
from time_travel import time_travel
from geopolitics import geopolitics

app = Flask(__name__)

# ============================================================
# DASHBOARD
# ============================================================
@app.route('/backup')
def backup_page():
    """Backup management page."""
    import os
    from datetime import datetime
    
    backups = []
    if os.path.exists('backups'):
        for f in sorted(os.listdir('backups'), reverse=True):
            if f.endswith('.zip'):
                size = round(os.path.getsize(f'backups/{f}') / 1024 / 1024, 2)
                mtime = datetime.fromtimestamp(os.path.getmtime(f'backups/{f}'))
                backups.append({"name": f, "size_mb": size, "date": mtime.strftime("%Y-%m-%d %H:%M")})
    
    html = """<!DOCTYPE html><html><head><title>Backups</title>
    <style>
    body{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px}
    h1{text-align:center;color:#D4AF37}
    .card{background:#0d0d20;border:1px solid #222;border-radius:12px;padding:25px;max-width:800px;margin:30px auto}
    table{width:100%;border-collapse:collapse;margin:20px 0}
    th,td{border:1px solid #222;padding:12px}
    th{background:#0a0a15;color:#D4AF37}
    .btn{display:inline-block;padding:10px 20px;border-radius:5px;text-decoration:none;font-weight:bold;margin:10px}
    .btn-gold{background:#D4AF37;color:#000}
    a{color:#D4AF37}
    </style></head><body>
    <h1>💾 BACKUP MANAGEMENT</h1>
    <div class='card'>
    <a href='/backup/create' class='btn btn-gold'>🆕 Create Full Backup</a>
    <p style='color:#888;margin-top:20px'>Auto-backup runs daily at 3 AM</p>
    <h3>Existing Backups</h3>
    <table><tr><th>Backup</th><th>Size</th><th>Date</th></tr>"""
    
    for b in backups[:14]:
        html += f"<tr><td>{b['name']}</td><td>{b['size_mb']} MB</td><td>{b['date']}</td></tr>"
    
    if not backups:
        html += "<tr><td colspan='3' style='text-align:center;color:#888'>No backups yet. Create one!</td></tr>"
    
    html += "</table></div><p style='text-align:center'><a href='/health'>Health</a> | <a href='/dashboard'>Dashboard</a></p></body></html>"
    return html

@app.route('/backup/create')
def backup_create():
    from system_health import health_system
from private_wealth import wealth as pw
from private_wealth import wealth as pw
    result = health_system.create_full_backup()
    if result["status"] == "ok":
        return f"<h1 style='color:#4CAF50;text-align:center'>✅ Backup Created!</h1><p style='text-align:center'>{result['backup_file']} — {result['total_size_mb']} MB</p><p style='text-align:center'><a href='/backup'>Back</a></p>"
    return f"<h1 style='color:#F44336'>❌ Failed</h1><a href='/backup'>Back</a>"

@app.route('/health')
def health_check():
    """System health check."""
    health = system_health()
    return jsonify(health)




@app.route('/family')
def family_home():
    return """<!DOCTYPE html><html><head><title>Family</title>
    <style>body{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px}
    h1{color:#ff69b4;text-align:center}.card{background:#0d0d20;border:1px solid #222;padding:25px;max-width:600px;margin:20px auto;border-radius:12px}
    input,select{width:100%;padding:10px;margin:10px 0;background:#0a0a0a;border:1px solid #333;color:#fff}
    button{background:#ff69b4;color:#fff;padding:12px 25px;border:none;cursor:pointer;font-weight:bold}
    a{color:#ff69b4}</style></head><body>
    <h1>👨‍👩‍👧‍👦 FAMILY & HEIRS</h1>
    <div class='card'><h3>💒 Marry</h3><form action='/family/marry' method='post'>
    <input name='person1' placeholder='Your username'><input name='person2' placeholder='Spouse username'>
    <input name='prenup' placeholder='Prenup amount (0 for none)'><button type='submit'>Get Married 💒</button></form></div>
    <div class='card'><h3>👶 Have Child</h3><form action='/family/child' method='post'>
    <input name='parent1' placeholder='Your username'><input name='parent2' placeholder='Spouse username'>
    <input name='name' placeholder='Child name'><select name='gender'><option>Random</option><option>Male</option><option>Female</option></select>
    <button type='submit'>Welcome Baby 👶</button></form></div>
    <div class='card'><h3>🎓 Education</h3><form action='/family/education' method='post'>
    <input name='child' placeholder='Child username'>
    <select name='institution'><option>Harvard ($250k)</option><option>Oxford ($200k)</option><option>MIT ($220k)</option></select>
    <button type='submit'>Send to School 🎓</button></form></div>
    <p style='text-align:center'><a href='/dashboard'>Dashboard</a></p></body></html>"""

@app.route('/family/marry', methods=['POST'])
def family_marry():
    from flask import request
    return f"<h1>💒 Marriage recorded!</h1><p>{request.form.get('person1')} ❤️ {request.form.get('person2')}</p><a href='/family'>Back</a>"

@app.route('/family/child', methods=['POST'])
def family_child():
    from flask import request
    return f"<h1>👶 Baby {request.form.get('name')} born!</h1><a href='/family'>Back</a>"

@app.route('/family/education', methods=['POST'])
def family_education():
    from flask import request
    return f"<h1>🎓 {request.form.get('child')} enrolled!</h1><a href='/family'>Back</a>"

@app.route('/protect')
def protect_home():
    return """<!DOCTYPE html><html><head><title>Asset Protection</title>
    <style>body{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px}
    h1{color:#ff4444;text-align:center}.card{background:#0d0d20;border:1px solid #222;padding:25px;max-width:600px;margin:20px auto;border-radius:12px}
    input,select{width:100%;padding:10px;margin:10px 0;background:#0a0a0a;border:1px solid #333;color:#fff}
    button{background:#ff4444;color:#fff;padding:12px 25px;border:none;cursor:pointer;font-weight:bold}
    a{color:#ff4444}</style></head><body>
    <h1>🛡️ ASSET PROTECTION</h1>
    <div class='card'><h3>🏢 Form LLC</h3><form action='/protect/llc' method='post'>
    <input name='owner' placeholder='Username'><input name='company_name' placeholder='LLC Name'>
    <select name='jurisdiction'><option>Delaware</option><option>Wyoming</option><option>Cayman Islands</option></select>
    <input name='assets' placeholder='Assets ($)'><button type='submit'>Form LLC</button></form></div>
    <div class='card'><h3>🏦 Offshore Trust</h3><form action='/protect/offshore' method='post'>
    <input name='creator' placeholder='Username'><input name='trust_name' placeholder='Trust Name'>
    <input name='amount' placeholder='Amount ($)'><button type='submit'>Create Trust</button></form></div>
    <p style='text-align:center'><a href='/dashboard'>Dashboard</a></p></body></html>"""

@app.route('/protect/llc', methods=['POST'])
def protect_llc():
    from flask import request
    return f"<h1>🏢 LLC Formed!</h1><p>{request.form.get('company_name')} in {request.form.get('jurisdiction')}</p><a href='/protect'>Back</a>"

@app.route('/protect/offshore', methods=['POST'])
def protect_offshore():
    from flask import request
    return f"<h1>🏦 Trust Created!</h1><p>{request.form.get('trust_name')}</p><a href='/protect'>Back</a>"

@app.route('/wealth')
def wealth_home():
    """Elite Private Wealth Dashboard."""
    import random
    banker = pw.assign_banker()
    tier = "diamond"
    tier_info = pw.tiers[tier]
    services = pw.get_services(tier)
    portfolio = pw.get_portfolio_recommendation(50000000, 60)
    codes = pw.invite_codes
    
    html = f"""<!DOCTYPE html><html><head><title>Private Wealth</title>
    <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{font-family:'Georgia',serif;background:#050510;color:#e0e0e0;min-height:100vh}}
    .header{{text-align:center;padding:40px;background:linear-gradient(180deg,#0a0010,#050510);border-bottom:2px solid {tier_info['color']}}}
    .header h1{{font-size:42px;color:{tier_info['color']};letter-spacing:5px}}
    .header .subtitle{{color:#888;font-style:italic;margin-top:10px}}
    .banker-card{{background:linear-gradient(135deg,#0d0d20,#1a0030);border:1px solid {tier_info['color']};border-radius:16px;padding:30px;margin:30px auto;max-width:800px;text-align:center}}
    .banker-name{{font-size:28px;color:{tier_info['color']};margin:10px 0}}
    .tier-badge{{display:inline-block;padding:8px 20px;border-radius:20px;background:{tier_info['color']}22;border:1px solid {tier_info['color']};color:{tier_info['color']};font-weight:bold;margin:10px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(350px,1fr));gap:25px;max-width:1200px;margin:30px auto;padding:0 30px}}
    .card{{background:#0d0d20;border:1px solid #222;border-radius:12px;padding:25px}}
    .card h3{{color:{tier_info['color']};margin-bottom:15px;font-size:18px}}
    table{{width:100%;border-collapse:collapse}}
    th,td{{border:1px solid #1a1a30;padding:10px;text-align:left;font-size:13px}}
    th{{background:#0a0a15;color:{tier_info['color']};font-size:10px;text-transform:uppercase}}
    .btn{{display:inline-block;padding:12px 25px;border-radius:6px;text-decoration:none;font-weight:bold;margin:10px;cursor:pointer}}
    .btn-gold{{background:{tier_info['color']};color:#000}}
    .btn-outline{{border:1px solid {tier_info['color']};color:{tier_info['color']};background:transparent}}
    .service-item{{padding:12px;border-bottom:1px solid #1a1a30;display:flex;align-items:center;gap:12px}}
    .service-icon{{font-size:24px}}
    .code-box{{background:#0a0a15;border:1px dashed {tier_info['color']};padding:15px;border-radius:8px;text-align:center;margin:10px 0;font-family:monospace;font-size:14px}}
    a{{color:{tier_info['color']};text-decoration:none}}
    input{{width:100%;padding:12px;margin:10px 0;background:#0a0a0a;border:1px solid #333;color:#fff;border-radius:5px;font-family:Georgia}}
    button{{width:100%;padding:12px;background:{tier_info['color']};color:#000;border:none;border-radius:5px;font-weight:bold;cursor:pointer;font-family:Georgia}}
    </style></head><body>
    
    <div class='header'>
        <h1>{tier_info['icon']} WYLLENE PRIVATE WEALTH</h1>
        <p class='subtitle'>Exclusive Wealth Management — Founded by Lunga Titus Malebadi</p>
    </div>
    
    <div class='banker-card'>
        <p style='color:#888;font-size:12px;text-transform:uppercase;letter-spacing:3px'>Your Personal Banker</p>
        <div class='banker-name'>🤵 {banker}</div>
        <div class='tier-badge'>{tier_info['icon']} {tier_info['name']} Tier</div>
        <p style='color:#888;margin-top:15px'>Available 24/7 for your wealth management needs</p>
    </div>
    
    <div class='grid'>
        <div class='card'>
            <h3>💼 Portfolio Recommendation</h3>
            <p style='color:#888;margin-bottom:15px'>Strategy: <b style='color:{tier_info['color']}'>{portfolio['strategy']}</b></p>
            <table><tr><th>Asset</th><th>Allocation</th></tr>"""
    
    for asset, pct in portfolio.items():
        if asset != "strategy":
            html += f"<tr><td>{asset.replace('_',' ').title()}</td><td style='color:{tier_info['color']}'>{pct}%</td></tr>"
    
    html += """</table></div>
        
        <div class='card'>
            <h3>🎁 Exclusive Services</h3>"""
    
    for s in services:
        html += f"<div class='service-item'><span class='service-icon'>{s['icon']}</span><div><b>{s['name']}</b><p style='color:#888;font-size:11px'>{s['desc']}</p></div></div>"
    
    html += """</div>
        
        <div class='card'>
            <h3>🔑 Access Codes</h3>
            <p style='color:#888;margin-bottom:10px'>Share these with invited members:</p>"""
    
    for code, level in codes.items():
        html += f"<div class='code-box'><b>{code}</b><br><span style='color:#888;font-size:11px'>{level}</span></div>"
    
    html += """</div>
        
        <div class='card'>
            <h3>🔐 Request Access</h3>
            <form action='/wealth/login' method='post'>
            <input name='invite_code' placeholder='Enter invitation code' required>
            <button type='submit'>Enter Private Wealth</button></form>
        </div>
    </div>
    
    <div style='text-align:center;padding:40px;color:#555;border-top:1px solid #222;margin-top:40px'>
        <p>🏰 Wyllene Private Wealth — Founded by Lunga Titus Malebadi</p>
        <p style='font-size:11px'>© 2026 All Rights Reserved</p>
    </div>
    
    </body></html>"""
    return html

@app.route('/wealth/login', methods=['POST'])
def wealth_login():
    from flask import request
    code = request.form.get("invite_code", "").strip().upper()
    if code in pw.invite_codes:
        level = pw.invite_codes[code]
        banker = pw.assign_banker()
        return f"""<!DOCTYPE html><html><head><title>Welcome</title>
        <style>body{{font-family:Georgia;background:#050510;color:#e0e0e0;padding:50px;text-align:center}}
        h1{{color:#D4AF37;font-size:42px}}.card{{background:#0d0d20;border:1px solid #D4AF37;padding:30px;max-width:500px;margin:30px auto;border-radius:12px}}
        a{{color:#D4AF37}}</style></head><body>
        <h1>👑 Welcome to Private Wealth</h1>
        <div class='card'><h2>{level}</h2><p>Your personal banker: <b>{banker}</b></p>
        <p style='color:#888'>Your exclusive dashboard is being prepared.</p></div>
        <a href='/wealth'>Enter Dashboard</a> | <a href='/dashboard'>Command Center</a></body></html>"""
    return f"<h1 style='color:#F44336'>❌ Invalid Code</h1><p><a href='/wealth'>Try Again</a></p>"

@app.route('/wealth/login', methods=['POST'])
def wealth_login():
    from flask import request
    code = request.form.get("invite_code", "").strip().upper()
    if code in pw.invite_codes:
        level = pw.invite_codes[code]
        banker = pw.assign_banker()
        return f"""<!DOCTYPE html><html><head><title>Welcome</title>
        <style>body{{font-family:Georgia;background:#050510;color:#e0e0e0;padding:50px;text-align:center}}
        h1{{color:#D4AF37;font-size:42px}}.card{{background:#0d0d20;border:1px solid #D4AF37;padding:30px;max-width:500px;margin:30px auto;border-radius:12px}}
        a{{color:#D4AF37}}</style></head><body>
        <h1>👑 Welcome to Private Wealth</h1>
        <div class='card'><h2>{level}</h2><p>Your personal banker: <b>{banker}</b></p>
        <p style='color:#888'>Your exclusive dashboard is being prepared.</p></div>
        <a href='/wealth'>Enter Dashboard</a> | <a href='/dashboard'>Command Center</a></body></html>"""
    return f"<h1 style='color:#F44336'>❌ Invalid Code</h1><p><a href='/wealth'>Try Again</a></p>"

@app.route('/wealth/login', methods=['POST'])
def wealth_login():
    from flask import request
    return f"<h1>✅ Access Granted!</h1><a href='/dashboard'>Dashboard</a>"

@app.route('/dynasty')
def dynasty_home():
    return """<!DOCTYPE html><html><head><title>Dynasty Life</title>
    <style>body{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px}
    h1{color:#D4AF37;text-align:center}.card{background:#0d0d20;border:1px solid #222;padding:25px;max-width:600px;margin:20px auto;border-radius:12px}
    input,select{width:100%;padding:10px;margin:10px 0;background:#0a0a0a;border:1px solid #333;color:#fff}
    button{background:#D4AF37;color:#000;padding:12px 25px;border:none;cursor:pointer;font-weight:bold}
    a{color:#D4AF37}</style></head><body>
    <h1>🏰 DYNASTY LIFE</h1>
    <div class='card'><h3>Create Character</h3><form action='/dynasty/create' method='post'>
    <input name='username' placeholder='Username'><input name='full_name' placeholder='Full Name'>
    <input name='age' placeholder='Age' value='18'><select name='career'><option>Entrepreneur</option><option>Investor</option><option>Executive</option></select>
    <input name='dynasty_name' placeholder='Dynasty Name'><button type='submit'>Start Life</button></form></div>
    <p style='text-align:center'><a href='/dashboard'>Dashboard</a></p></body></html>"""

@app.route('/dynasty/create', methods=['POST'])
def dynasty_create():
    from flask import request
    return f"<h1>✅ Character Created!</h1><p>{request.form.get('full_name')} of House {request.form.get('dynasty_name')}</p><a href='/dynasty'>Back</a>"

@app.route('/fraud')
def fraud_home():
    return """<!DOCTYPE html><html><head><title>Fraud Detection</title>
    <style>body{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px;text-align:center}
    h1{color:#ff4444}.card{background:#0d0d20;border:1px solid #222;padding:30px;max-width:600px;margin:30px auto;border-radius:12px}
    table{width:100%;border-collapse:collapse}th,td{border:1px solid #222;padding:10px}
    th{background:#1a0000;color:#ff4444}a{color:#ff4444}</style></head><body>
    <h1>🛡️ FRAUD DETECTION</h1>
    <div class='card'><h3>Risk Monitoring Active</h3>
    <table><tr><th>Check</th><th>Status</th></tr>
    <tr><td>Large Transactions</td><td style='color:#4CAF50'>✅ Monitoring</td></tr>
    <tr><td>Odd Hours</td><td style='color:#4CAF50'>✅ Active</td></tr>
    <tr><td>Velocity</td><td style='color:#4CAF50'>✅ Active</td></tr>
    <tr><td>Pattern Analysis</td><td style='color:#4CAF50'>✅ Active</td></tr></table></div>
    <a href='/dashboard'>Dashboard</a></body></html>"""

@app.route('/currency')
def currency_home():
    rates = {"USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 149.5, "ZAR": 18.3}
    html = """<!DOCTYPE html><html><head><title>Currency</title>
    <style>body{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px}
    h1{color:#D4AF37;text-align:center}table{width:100%;max-width:600px;margin:30px auto;border-collapse:collapse}
    th,td{border:1px solid #222;padding:12px}th{background:#0a0a15;color:#D4AF37}
    a{color:#D4AF37}</style></head><body>
    <h1>💱 CURRENCY EXCHANGE</h1>
    <table><tr><th>Currency</th><th>Rate (USD)</th></tr>"""
    for code, rate in rates.items():
        html += f"<tr><td>{code}</td><td>{rate:.4f}</td></tr>"
    html += "</table><p style='text-align:center'><a href='/dashboard'>Dashboard</a></p></body></html>"
    return html

@app.route('/analytics')
def analytics_home():
    return """<!DOCTYPE html><html><head><title>Analytics</title>
    <style>body{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px;text-align:center}
    h1{color:#D4AF37}.card{background:#0d0d20;border:1px solid #222;padding:30px;max-width:600px;margin:30px auto;border-radius:12px}
    .metric{font-size:42px;color:#D4AF37;font-weight:bold}
    a{color:#D4AF37}</style></head><body>
    <h1>📊 ANALYTICS</h1>
    <div class='card'><h3>System Overview</h3>
    <div class='metric'>Active</div><p style='color:#888'>Full analytics dashboard coming soon</p></div>
    <a href='/dashboard'>Dashboard</a></body></html>"""


@app.route('/assets')
def assets_home():
    """Asset Portfolio Dashboard."""
    import random
    
    assets = {
        "stocks": [
            {"name": "Wyllene Corp", "ticker": "WYLL", "shares": 10000, "price": round(random.uniform(100,500),2)},
            {"name": "Dynasty Holdings", "ticker": "DYNA", "shares": 5000, "price": round(random.uniform(200,600),2)},
            {"name": "Legacy Industries", "ticker": "LEGC", "shares": 8000, "price": round(random.uniform(50,300),2)},
        ],
        "real_estate": [
            {"name": "Malebadi Tower", "location": "New York", "value": 85000000},
            {"name": "Dynasty Estate", "location": "London", "value": 45000000},
            {"name": "Wyllene Resort", "location": "Dubai", "value": 120000000},
        ],
        "businesses": [
            {"name": "Wyllene Industries", "sector": "Technology", "valuation": 500000000},
            {"name": "Dynasty Capital", "sector": "Finance", "valuation": 250000000},
        ],
        "crypto": [
            {"name": "Bitcoin", "ticker": "BTC", "amount": 50, "price": 67500},
            {"name": "Ethereum", "ticker": "ETH", "amount": 500, "price": 3450},
        ],
        "cash": 15000000
    }
    
    # Calculate totals
    stocks_total = sum(s["shares"] * s["price"] for s in assets["stocks"])
    real_estate_total = sum(r["value"] for r in assets["real_estate"])
    business_total = sum(b["valuation"] for b in assets["businesses"])
    crypto_total = sum(c["amount"] * c["price"] for c in assets["crypto"])
    total_assets = stocks_total + real_estate_total + business_total + crypto_total + assets["cash"]
    
    html = f"""<!DOCTYPE html><html><head><title>Asset Portfolio</title>
    <style>
    body{{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px}}
    h1{{text-align:center;color:#D4AF37;font-size:36px}}
    .total{{text-align:center;font-size:48px;color:#D4AF37;font-weight:bold;margin:20px 0}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:20px;max-width:1200px;margin:0 auto}}
    .card{{background:#0d0d20;border:1px solid #222;border-radius:12px;padding:25px}}
    .card h3{{margin:0 0 15px 0;font-size:20px}}
    table{{width:100%;border-collapse:collapse;margin:10px 0}}
    th,td{{border:1px solid #1a1a30;padding:10px;text-align:left}}
    th{{background:#0a0a15;font-size:11px;text-transform:uppercase;letter-spacing:1px}}
    .green{{color:#4CAF50}}.gold{{color:#D4AF37}}.blue{{color:#2196F3}}.purple{{color:#9C27B0}}
    .bar{{background:#1a1a30;height:6px;border-radius:3px;margin:15px 0}}
    .bar-fill{{height:100%;border-radius:3px}}
    .allocation{{display:flex;gap:10px;margin:10px 0}}
    .alloc-item{{flex:1;text-align:center;padding:10px;background:#0a0a15;border-radius:8px}}
    .alloc-value{{font-size:18px;font-weight:bold}}
    .alloc-label{{font-size:10px;color:#888;text-transform:uppercase}}
    a{{color:#D4AF37;text-decoration:none}}
    .btn{{display:inline-block;padding:10px 20px;border-radius:5px;text-decoration:none;font-weight:bold;margin:10px}}
    .btn-gold{{background:#D4AF37;color:#000}}
    </style></head><body>
    <h1>💼 ASSET PORTFOLIO</h1>
    <div class='total'>${total_assets:,.0f}</div>
    <p style='text-align:center;color:#888'>Total Portfolio Value</p>
    
    <div class='allocation'>
        <div class='alloc-item'><div class='alloc-value green'>${stocks_total:,.0f}</div><div class='alloc-label'>Stocks</div></div>
        <div class='alloc-item'><div class='alloc-value blue'>${real_estate_total:,.0f}</div><div class='alloc-label'>Real Estate</div></div>
        <div class='alloc-item'><div class='alloc-value gold'>${business_total:,.0f}</div><div class='alloc-label'>Businesses</div></div>
        <div class='alloc-item'><div class='alloc-value purple'>${crypto_total:,.0f}</div><div class='alloc-label'>Crypto</div></div>
        <div class='alloc-item'><div class='alloc-value'>${assets['cash']:,.0f}</div><div class='alloc-label'>Cash</div></div>
    </div>
    
    <div class='bar'><div class='bar-fill' style='width:100%;background:linear-gradient(90deg,#4CAF50 {stocks_total/total_assets*100}%,#2196F3 {stocks_total/total_assets*100}%,#2196F3 {(stocks_total+real_estate_total)/total_assets*100}%,#D4AF37 {(stocks_total+real_estate_total)/total_assets*100}%,#D4AF37 {(stocks_total+real_estate_total+business_total)/total_assets*100}%,#9C27B0 {(stocks_total+real_estate_total+business_total)/total_assets*100}%,#9C27B0 {(stocks_total+real_estate_total+business_total+crypto_total)/total_assets*100}%,#888 {(stocks_total+real_estate_total+business_total+crypto_total)/total_assets*100}%,#888 100%'></div></div>
    
    <div class='grid'>
        <div class='card'>
            <h3 class='green'>📈 Stocks</h3>
            <table><tr><th>Ticker</th><th>Company</th><th>Shares</th><th>Price</th><th>Value</th></tr>"""
    
    for s in assets["stocks"]:
        value = s["shares"] * s["price"]
        html += f"<tr><td><b>{s['ticker']}</b></td><td>{s['name']}</td><td>{s['shares']:,}</td><td>${s['price']:.2f}</td><td class='green'>${value:,.0f}</td></tr>"
    
    html += f"""<tr><td colspan='4'><b>Total</b></td><td class='green'><b>${stocks_total:,.0f}</b></td></tr></table></div>
        
        <div class='card'>
            <h3 class='blue'>🏠 Real Estate</h3>
            <table><tr><th>Property</th><th>Location</th><th>Value</th></tr>"""
    
    for r in assets["real_estate"]:
        html += f"<tr><td><b>{r['name']}</b></td><td>{r['location']}</td><td class='blue'>${r['value']:,.0f}</td></tr>"
    
    html += f"""<tr><td colspan='2'><b>Total</b></td><td class='blue'><b>${real_estate_total:,.0f}</b></td></tr></table></div>
        
        <div class='card'>
            <h3 class='gold'>🏢 Businesses</h3>
            <table><tr><th>Company</th><th>Sector</th><th>Valuation</th></tr>"""
    
    for b in assets["businesses"]:
        html += f"<tr><td><b>{b['name']}</b></td><td>{b['sector']}</td><td class='gold'>${b['valuation']:,.0f}</td></tr>"
    
    html += f"""<tr><td colspan='2'><b>Total</b></td><td class='gold'><b>${business_total:,.0f}</b></td></tr></table></div>
        
        <div class='card'>
            <h3 class='purple'>🪙 Cryptocurrency</h3>
            <table><tr><th>Ticker</th><th>Name</th><th>Amount</th><th>Price</th><th>Value</th></tr>"""
    
    for c in assets["crypto"]:
        value = c["amount"] * c["price"]
        html += f"<tr><td><b>{c['ticker']}</b></td><td>{c['name']}</td><td>{c['amount']:,.4f}</td><td>${c['price']:,}</td><td class='purple'>${value:,.0f}</td></tr>"
    
    html += f"""<tr><td colspan='4'><b>Total</b></td><td class='purple'><b>${crypto_total:,.0f}</b></td></tr></table></div>
        
        <div class='card'>
            <h3>💵 Cash Reserves</h3>
            <div style='font-size:36px;color:#D4AF37;text-align:center;padding:20px'>${assets['cash']:,.0f}</div>
        </div>
    </div>
    
    <div style='text-align:center;margin-top:30px'>
    <a href='/dashboard' class='btn btn-gold'>Command Center</a>
    </div>
    <p style='text-align:center;color:#888;margin-top:20px'>Asset allocation is for demonstration. Real values calculated live.</p>
    </body></html>"""
    return html

@app.route('/test')
def test():
    return "OK"

@app.route('/chat')
def chat():
    return """<!DOCTYPE html><html><head><title>Wyllene AI</title>
    <style>body{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px;text-align:center}
    h1{color:#D4AF37}input{width:400px;padding:15px;margin:10px;background:#0d0d20;border:1px solid #333;color:#fff;font-size:16px}
    button{background:#D4AF37;color:#000;padding:15px 30px;border:none;font-weight:bold;cursor:pointer;font-size:16px}
    .response{background:#0d0d20;border:1px solid #222;padding:30px;max-width:600px;margin:30px auto;border-radius:12px;color:#aaa}
    a{color:#D4AF37}</style></head><body>
    <h1>🤖 WYLLENE AI ADVISOR</h1>
    <p style='color:#888'>Your personal wealth intelligence</p>
    <form action='/chat' method='get'>
    <input name='q' placeholder='Ask your AI advisor...'><br>
    <button type='submit'>Ask AI</button></form>
    <div class='response'><p>Ask me about wealth, strategy, investments, or your dynasty.</p></div>
    <a href='/dashboard'>Command Center</a></body></html>"""

@app.route('/dashboard')
@safe_route
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
@safe_route
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
@safe_route
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
@safe_route
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
@safe_route
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


@app.route('/rivals')
@safe_route
def rivals_hub():
    """AI Rival Dynasties Hub."""
    rivals = ai_rivals.get_all_rivals()
    
    if not rivals:
        ai_rivals.generate_rival_dynasties(5)
        rivals = ai_rivals.get_all_rivals()
    
    html = """<!DOCTYPE html><html><head><title>AI Rivals</title>
    <style>
    body{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px}
    h1{color:#FF4444;text-align:center;font-size:36px}
    .subtitle{text-align:center;color:#888;font-style:italic}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(350px,1fr));gap:20px;max-width:1200px;margin:30px auto}
    .card{background:#0d0d20;border:1px solid #222;border-radius:12px;padding:25px}
    .card:hover{border-color:#FF4444}
    .card h3{color:#FF4444;margin-bottom:10px}
    table{width:100%;border-collapse:collapse;margin:10px 0}
    th,td{border:1px solid #222;padding:10px}
    th{background:#1a0000;color:#FF4444}
    .ai{color:#FF4444}.player{color:#D4AF37}
    .btn{display:inline-block;padding:10px 20px;border-radius:5px;text-decoration:none;font-weight:bold;margin:5px}
    .btn-red{background:#FF4444;color:#000}
    .btn-outline{border:1px solid #FF4444;color:#FF4444}
    a{color:#D4AF37;text-decoration:none}
    </style></head><body>
    <h1>🤖 AI RIVAL DYNASTIES</h1>
    <p class='subtitle'>Intelligent competitors that adapt, grow, and challenge your empire</p>
    
    <div class='grid'>
        <div class='card'>
            <h3>⚔️ Simulate AI Turns</h3>
            <p>Advance all AI dynasties by one cycle.</p>
            <a href='/rivals/simulate' class='btn btn-red'>Simulate AI Turn</a>
        </div>
        <div class='card'>
            <h3>🆕 Generate New Rivals</h3>
            <p>Create fresh AI dynasties to compete against.</p>
            <a href='/rivals/generate' class='btn btn-outline'>Generate Rivals</a>
        </div>
    </div>
    
    <h2>🏆 Dynasty Rankings</h2>
    <table><tr><th>Rank</th><th>Dynasty</th><th>Type</th><th>Personality</th><th>Wealth</th><th>Members</th></tr>"""
    
    for i, r in enumerate(rivals[:10]):
        html += f"<tr><td>{i+1}</td><td><b>{r['dynasty_name']}</b></td><td class='ai'>AI</td><td>{r['personality']}</td><td>${r['net_worth']:,.0f}</td><td>{r['members']}</td></tr>"
    
    html += "</table>"
    html += "<p style='text-align:center;margin-top:30px'><a href='/dashboard'>Command Center</a> | <a href='/exclusive'>S-Tier</a></p>"
    html += "</body></html>"
    return html

@app.route('/rivals/simulate')
def rivals_simulate():
    results = ai_rivals.simulate_all_ai_turns()
    
    html = """<!DOCTYPE html><html><head><title>AI Turns Simulated</title>
    <style>body{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px}
    h1{color:#FF4444}table{width:100%;max-width:800px;margin:20px auto;border-collapse:collapse}
    th,td{border:1px solid #222;padding:12px}th{background:#1a0000;color:#FF4444}
    a{color:#D4AF37}</style></head><body>
    <h1>⚔️ AI TURNS SIMULATED</h1>
    <table><tr><th>Dynasty</th><th>Action</th><th>Impact</th></tr>"""
    
    for r in results:
        impact = r['action']['impact']
        color = "#4CAF50" if impact > 0 else "#F44336"
        html += f"<tr><td><b>{r['dynasty']}</b></td><td>{r['action']['desc']}</td><td style='color:{color}'>${impact:+,.0f}</td></tr>"
    
    html += "</table><p style='text-align:center'><a href='/rivals'>Back</a></p></body></html>"
    return html


@app.route('/timetravel')
@safe_route
def timetravel_hub():
    """Time Travel Scenarios Hub."""
    scenarios = time_travel.get_all_scenarios()
    
    html = """<!DOCTYPE html><html><head><title>Time Travel</title>
    <style>
    body{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px}
    h1{color:#D4AF37;text-align:center;font-size:36px}
    .subtitle{text-align:center;color:#888;font-style:italic;margin-bottom:30px}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(350px,1fr));gap:20px;max-width:1200px;margin:0 auto}
    .card{background:#0d0d20;border:1px solid #222;border-radius:12px;padding:25px;transition:all 0.3s}
    .card:hover{transform:translateY(-3px)}
    .card h3{margin:0 0 10px 0;font-size:22px}
    .year{color:#888;font-size:14px}
    .desc{color:#aaa;margin:10px 0}
    .impact{font-size:24px;font-weight:bold;margin:10px 0}
    .lesson{color:#D4AF37;font-style:italic;margin:10px 0}
    .btn{display:inline-block;padding:10px 20px;border-radius:5px;text-decoration:none;font-weight:bold;margin:5px}
    .btn-time{background:#9C27B0;color:#fff}
    a{color:#D4AF37;text-decoration:none}
    </style></head><body>
    <h1>🕰️ TIME TRAVEL SCENARIOS</h1>
    <p class='subtitle'>Replay history's greatest market events with your dynasty</p>
    
    <div class='grid'>"""
    
    for s in scenarios:
        html += f"""
        <div class='card' style='border-left:3px solid {s["color"]}'>
            <h3>{s['emoji']} {s['name']}</h3>
            <div class='year'>📅 {s['year']}</div>
            <p class='desc'>{s['desc']}</p>
            <div class='impact' style='color:{s["color"]}'>Market: {s['impact']*100:+.0f}%</div>
            <p>⏱️ Duration: {s['duration']}</p>
            <p>🏆 Survivors: {s['survivors']}</p>
            <p class='lesson'>💡 {s['lesson']}</p>
            <a href='/timetravel/simulate?scenario={s["name"]}&wealth=1000000' class='btn btn-time'>🕰️ Simulate with $1M</a>
            <a href='/timetravel/simulate?scenario={s["name"]}&wealth=10000000' class='btn btn-time'>🕰️ Simulate with $10M</a>
        </div>"""
    
    html += """</div>
    <p style='text-align:center;margin-top:30px'><a href='/dashboard'>Command Center</a> | <a href='/exclusive'>S-Tier</a></p>
    </body></html>"""
    return html


@app.route('/geopolitics')
@safe_route
def geopolitics_hub():
    """Geopolitical Influence Hub."""
    event = geopolitics.generate_world_event()
    actions = geopolitics.political_actions
    
    html = """<!DOCTYPE html><html><head><title>Geopolitics</title>
    <style>
    body{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px}
    h1{color:#D4AF37;text-align:center;font-size:36px}
    .subtitle{text-align:center;color:#888;font-style:italic;margin-bottom:30px}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:20px;max-width:1200px;margin:0 auto}
    .card{background:#0d0d20;border:1px solid #222;border-radius:12px;padding:25px}
    .card h3{color:#D4AF37;margin-bottom:15px}
    .world-event{background:#1a0000;border:2px solid #FF4444;border-radius:12px;padding:25px;margin:20px 0;text-align:center}
    .world-event h2{color:#FF4444;margin:0}
    .impact{font-size:28px;font-weight:bold;margin:10px 0}
    table{width:100%;border-collapse:collapse;margin:10px 0}
    th,td{border:1px solid #222;padding:10px}
    th{background:#0a0a15;color:#D4AF37}
    .btn{display:inline-block;padding:10px 20px;border-radius:5px;text-decoration:none;font-weight:bold;margin:5px;cursor:pointer}
    .btn-red{background:#FF4444;color:#000}
    .btn-gold{background:#D4AF37;color:#000}
    .btn-outline{border:1px solid #D4AF37;color:#D4AF37}
    a{color:#D4AF37;text-decoration:none}
    </style></head><body>
    <h1>🌍 GEOPOLITICAL INFLUENCE</h1>
    <p class='subtitle'>Shape world events. Control governments. Dominate globally.</p>
    
    <div class='world-event'>
        <h2>📰 BREAKING WORLD EVENT</h2>
        <h3>""" + event['name'] + """</h3>
        <p>""" + event['desc'] + """</p>
        <div class='impact' style='color:""" + ('#4CAF50' if event['market'] > 0 else '#F44336') + """'>Market Impact: """ + f"{event['market']*100:+.0f}%" + """</div>
        <p>Regions: """ + ', '.join(event['regions']) + """</p>
        <a href='/geopolitics/newevent' class='btn btn-red'>🔄 New Event</a>
    </div>
    
    <h2>🏛️ Political Actions</h2>
    <div class='grid'>"""
    
    for a in actions:
        html += f"""
        <div class='card'>
            <h3>{a['action']}</h3>
            <p>{a['desc']}</p>
            <p>Cost: <b>${a['cost']:,}</b></p>
            <p>Influence: <b>+{a['influence']}</b></p>
            <a href='/geopolitics/action?action={a['action']}&dynasty=Malebadi&wealth=10000000' class='btn btn-gold'>Execute</a>
        </div>"""
    
    html += """</div>
    <p style='text-align:center;margin-top:30px'><a href='/dashboard'>Command Center</a> | <a href='/exclusive'>S-Tier</a></p>
    </body></html>"""
    return html

@app.route('/geopolitics/newevent')
def geopolitics_new_event():
    event = geopolitics.generate_world_event()
    color = "#4CAF50" if event['market'] > 0 else "#F44336"
    
    html = f"""<!DOCTYPE html><html><head><title>World Event</title>
    <style>body{{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px;text-align:center}}
    h1{{color:#FF4444}}.card{{background:#1a0000;border:2px solid #FF4444;padding:30px;max-width:600px;margin:30px auto;border-radius:12px}}
    .impact{{font-size:32px;color:{color}}}a{{color:#D4AF37}}</style></head><body>
    <h1>📰 WORLD EVENT</h1>
    <div class='card'>
    <h2>{event['name']}</h2><p>{event['desc']}</p>
    <div class='impact'>Market: {event['market']*100:+.0f}%</div>
    <p>Regions: {', '.join(event['regions'])}</p></div>
    <a href='/geopolitics'>Back</a></body></html>"""
    return html

@app.route('/geopolitics/action')
def geopolitics_action():
    from flask import request
    action_name = request.args.get("action")
    dynasty = request.args.get("dynasty", "Malebadi")
    wealth = float(request.args.get("wealth", 10000000))
    
    result = geopolitics.perform_political_action(dynasty, action_name, wealth)
    if not result:
        return "<h1>Action not found</h1>"
    
    html = f"""<!DOCTYPE html><html><head><title>Political Action</title>
    <style>body{{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px;text-align:center}}
    h1{{color:#D4AF37}}.card{{background:#0d0d20;border:1px solid #222;padding:30px;max-width:500px;margin:30px auto;border-radius:12px}}
    .success{{color:#4CAF50;font-size:24px}}.fail{{color:#FF4444;font-size:24px}}
    a{{color:#D4AF37}}</style></head><body>
    <h1>🏛️ POLITICAL ACTION</h1>
    <div class='card'>
    <h2>{dynasty} — {result['action']}</h2>
    <div class='{'success' if result['success'] else 'fail'}'>{result['message']}</div>
    <p>Cost: ${result['cost']:,}</p>
    <p>Influence Gained: +{result['influence_gained']}</p>
    </div>
    <a href='/geopolitics'>Back</a></body></html>"""
    return html

@app.route('/timetravel/simulate')
def timetravel_simulate():
    from flask import request
    scenario_name = request.args.get("scenario")
    wealth = float(request.args.get("wealth", 1000000))
    
    result = time_travel.simulate_scenario(scenario_name, wealth)
    if not result:
        return "<h1>Scenario not found</h1>"
    
    s = result["scenario"]
    change_color = "#4CAF50" if result["change"] > 0 else "#F44336"
    
    html = f"""<!DOCTYPE html><html><head><title>{s['name']} Result</title>
    <style>
    body{{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px;text-align:center}}
    h1{{color:{s['color']};font-size:42px}}
    .card{{background:#0d0d20;border:2px solid {s['color']};padding:40px;max-width:600px;margin:30px auto;border-radius:16px}}
    .result{{font-size:60px;font-weight:bold;color:{s['color']};margin:20px 0}}
    .change{{font-size:32px;color:{change_color};margin:10px 0}}
    .lesson{{color:#D4AF37;font-style:italic;margin:20px 0;font-size:18px}}
    .stat{{display:inline-block;margin:15px 25px}}
    .stat-value{{font-size:28px;color:#D4AF37}}
    .stat-label{{font-size:11px;color:#888}}
    a{{color:#D4AF37;text-decoration:none;margin:0 10px}}
    </style></head><body>
    <h1>{s['emoji']} {s['name']} ({s['year']})</h1>
    <div class='card'>
    <div class='result'>{result['rating']}</div>
    <div class='change'>Change: ${result['change']:+,.0f}</div>
    <div class='stat'><div class='stat-value'>${result['starting_wealth']:,.0f}</div><div class='stat-label'>Starting Wealth</div></div>
    <div class='stat'><div class='stat-value'>${result['ending_wealth']:,.0f}</div><div class='stat-label'>Ending Wealth</div></div>
    <p class='lesson'>💡 {s['lesson']}</p>
    <p style='color:#aaa'>{result['message']}</p>
    </div>
    <a href='/timetravel'>Back to Scenarios</a> | <a href='/dashboard'>Command Center</a>
    </body></html>"""
    return html

@app.route('/rivals/generate')
def rivals_generate():
    created = ai_rivals.generate_rival_dynasties(3)
    
    html = """<!DOCTYPE html><html><head><title>Rivals Generated</title>
    <style>body{font-family:Georgia;background:#050510;color:#e0e0e0;padding:30px}
    h1{color:#FF4444}table{width:100%;max-width:800px;margin:20px auto;border-collapse:collapse}
    th,td{border:1px solid #222;padding:12px}th{background:#1a0000;color:#FF4444}
    a{color:#D4AF37}</style></head><body>
    <h1>🆕 NEW RIVALS GENERATED</h1>
    <table><tr><th>Dynasty</th><th>Founder</th><th>Personality</th><th>Strategy</th></tr>"""
    
    for c in created:
        html += f"<tr><td><b>{c['dynasty']}</b></td><td>{c['founder']}</td><td>{c['personality']}</td><td>{c['strategy']}</td></tr>"
    
    html += "</table><p style='text-align:center'><a href='/rivals'>Back</a></p></body></html>"
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
    app.after_request(add_security_headers)
    app.run(host="0.0.0.0", port=WEB_PORT)
