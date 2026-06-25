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
if __name__ == "__main__":
    print("🏰 Wyllene Dynasty Starting...")
    initialize()
    threading.Thread(target=start_socket, daemon=True).start()
    app.run(host="0.0.0.0", port=WEB_PORT)
