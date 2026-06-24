"""Wyllene ATM Bot — locked to owner only, no spam."""
import requests, json, socket, time

TOKEN = "8980273422:AAG7c84_OTsFSXnWGLzF-2nSGd8mOfrS0eA"
HOST = "localhost"
PORT = 9999
OWNER_ID = 6819329002  # Only you

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def send_to_server(cmd):
    try:
        s = socket.socket(); s.settimeout(5)
        s.connect((HOST, PORT)); s.sendall(json.dumps(cmd).encode())
        resp = json.loads(s.recv(8192).decode()); s.close()
        return resp
    except:
        return {"status": "error", "message": "Server offline"}

# Wait for server
print("⏳ Waiting for server...")
for i in range(30):
    try:
        s = socket.socket(); s.settimeout(3)
        s.connect((HOST, PORT)); s.close()
        break
    except:
        time.sleep(2)

print("🤖 Bot started — spam filtered")
offset = 0

while True:
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        resp = requests.get(url, params={"offset": offset, "timeout": 30})
        data = resp.json()
        
        if data.get("ok") and data.get("result"):
            for update in data["result"]:
                offset = update["update_id"] + 1
                
                if "message" not in update:
                    continue
                
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "").strip()
                
                # BLOCK EVERYONE EXCEPT YOU
                if chat_id != OWNER_ID:
                    print(f"🚫 Blocked spam from {chat_id}")
                    continue
                
                # Only respond to your messages
                print(f"📩 You: {text}")
                
                if text == "/start":
                    send_message(chat_id, "🏦 Welcome to Wyllene ATM!\n\nCommands:\n/login — Log in\n/balance — Check balance\n/deposit <amount>\n/withdraw <amount>")
                elif text == "/login":
                    send_message(chat_id, "Send your username:")
                elif text == "/balance":
                    resp = send_to_server({"cmd": "BALANCE"})
                    send_message(chat_id, f"💰 Balance: ${resp.get('balance', 0):,.2f}")
                else:
                    send_message(chat_id, f"Received: {text}")
        
        time.sleep(0.5)
    
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(2)
