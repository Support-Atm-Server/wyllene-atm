#!/usr/bin/env python3
"""
Wyllene ATM Bot — Single instance, named, clean.
"""
import requests
import json
import socket
import time
import sys

# ---- CONFIG ----
TOKEN = "8980273422:AAG7c84_OTsFSXnWGLzF-2nSGd8mOfrS0eA"
OWNER_ID = 6819329002
HOST = "localhost"
PORT = 9999

# ---- HELPERS ----
def telegram(method, data=None):
    """Call Telegram API."""
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    try:
        if data:
            r = requests.post(url, json=data, timeout=10)
        else:
            r = requests.get(url, timeout=10)
        return r.json()
    except Exception as e:
        print(f"Network error: {e}")
        return {"ok": False}

def send_msg(chat_id, text):
    """Send a message."""
    return telegram("sendMessage", {"chat_id": chat_id, "text": text})

def server_cmd(cmd):
    """Send command to socket server."""
    try:
        s = socket.socket()
        s.settimeout(3)
        s.connect((HOST, PORT))
        s.sendall(json.dumps(cmd).encode())
        r = json.loads(s.recv(4096).decode())
        s.close()
        return r
    except:
        return {"status": "error", "message": "Server offline"}

# ---- MAIN ----
def main():
    print("=" * 50)
    print("   🏦 WYLLENE ATM BOT")
    print("   Single Instance — Owner Only")
    print("=" * 50)
    
    # Wait for server
    print("⏳ Waiting for server...")
    for i in range(20):
        try:
            s = socket.socket()
            s.settimeout(3)
            s.connect((HOST, PORT))
            s.close()
            print("✅ Server connected")
            break
        except:
            time.sleep(2)
    else:
        print("❌ Server not found. Start server.py first.")
        sys.exit(1)
    
    print("🤖 Bot is LIVE — Send /start on Telegram")
    offset = 0
    
    while True:
        try:
            # Get updates
            resp = telegram("getUpdates", {"offset": offset, "timeout": 30})
            
            if not resp.get("ok"):
                time.sleep(2)
                continue
            
            for update in resp.get("result", []):
                offset = update["update_id"] + 1
                
                msg = update.get("message")
                if not msg:
                    continue
                
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "").strip()
                
                # Only respond to owner
                if chat_id != OWNER_ID:
                    print(f"🚫 Blocked: {chat_id}")
                    continue
                
                print(f"📩 You: {text}")
                
                # Commands
                if text == "/start":
                    send_msg(chat_id, "🏦 *Wyllene ATM*\n\nWelcome! Type /help for commands.")
                elif text == "/help":
                    send_msg(chat_id, """🏦 *Wyllene ATM Commands*

*Banking:*
/balance — Check balance
/deposit <amount> — Add funds
/withdraw <amount> — Take funds
/transfer <user> <amount> — Send money

*Currency & Crypto:*
/rates — Exchange rates
/crypto — Crypto prices
/convert <from> <to> <amount> — Convert currency
/buy <crypto> <usd> — Buy crypto
/sell <crypto> <amount> — Sell crypto
/balances — All balances

*Analytics:*
/stats — Your spending stats
/report — Transaction summary""")
                elif text == "/balance":
                    r = server_cmd({"cmd": "BALANCE"})
                    send_msg(chat_id, f"💰 Balance: ${r.get('balance', 0):,.2f}")
                elif text == "/ping":
                    send_msg(chat_id, "🏓 Pong!")
                elif text == "/stats":
                    r = server_cmd({"cmd": "USER_ANALYTICS", "username": "wyllene"})
                    if r.get("status") == "ok":
                        s = r["stats"]
                        msg = f"📊 *Your Stats (30 days)*\n"
                        msg += f"Transactions: {s['count']}\n"
                        msg += f"Total: ${s['total']:,.2f}\n"
                        msg += f"Average: ${s['avg']:,.2f}\n"
                        msg += f"Largest: ${s['max']:,.2f}"
                        send_msg(chat_id, msg)
                    else:
                        send_msg(chat_id, "Could not load stats.")
                elif text == "/report":
                    r = server_cmd({"cmd": "TRANSACTION_SUMMARY"})
                    if r.get("status") == "ok":
                        summary = r["summary"]
                        msg = "📊 *Transaction Summary (30 days)*\n"
                        for t, data in summary["by_type"].items():
                            msg += f"\n{t}: ${data['total']:,.2f} ({data['count']} txns)"
                        send_msg(chat_id, msg)
                    else:
                        send_msg(chat_id, "Could not load report.")
                elif text == "/rates":
                    r = server_cmd({"cmd": "FIAT_RATES"})
                    if r.get("status") == "ok":
                        msg = "💱 *Exchange Rates*\n"
                        for code, rate in list(r["rates"].items())[:10]:
                            msg += f"\n{code}: {rate:.4f}"
                        send_msg(chat_id, msg)
                elif text == "/crypto":
                    r = server_cmd({"cmd": "CRYPTO_PRICES"})
                    if r.get("status") == "ok":
                        msg = "🪙 *Crypto Prices*\n"
                        for code, price in r["prices"].items():
                            msg += f"\n{code}: ${price:,.2f}"
                        send_msg(chat_id, msg)
                elif text == "/balances":
                    r = server_cmd({"cmd": "MY_BALANCES"})
                    if r.get("status") == "ok":
                        msg = "💼 *Your Balances*\n\n*Fiat:*\n"
                        for code, bal in r["fiat"].items():
                            if bal > 0:
                                msg += f"{code}: {bal:,.2f}\n"
                        msg += "\n*Crypto:*\n"
                        for code, bal in r["crypto"].items():
                            if bal > 0:
                                msg += f"{code}: {bal:.6f}\n"
                        send_msg(chat_id, msg)
                else:
                    send_msg(chat_id, f"Received: {text}\nType /help for commands.")
            
            time.sleep(0.3)
        
        except KeyboardInterrupt:
            print("\n👋 Bot stopped.")
            sys.exit(0)
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
