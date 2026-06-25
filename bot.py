"""Ultra-minimal bot — cannot spam."""
import requests, json, socket, time, sys

TOKEN = "8980273422:AAG7c84_OTsFSXnWGLzF-2nSGd8mOfrS0eA"
OWNER = 6819329002

def api(method, data=None):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    r = requests.post(url, json=data) if data else requests.get(url)
    return r.json()

def server_cmd(cmd):
    try:
        s = socket.socket(); s.settimeout(3)
        s.connect(("localhost", 9999))
        s.sendall(json.dumps(cmd).encode())
        r = json.loads(s.recv(4096).decode())
        s.close()
        return r
    except:
        return {"status": "error"}

print("Bot starting...")
offset = 0
processed = set()

while True:
    try:
        resp = api("getUpdates", {"offset": offset, "timeout": 30})
        if not resp.get("ok"):
            time.sleep(1)
            continue
        
        for update in resp.get("result", []):
            uid = update["update_id"]
            
            # NEVER process the same update twice
            if uid in processed:
                continue
            processed.add(uid)
            offset = uid + 1
            
            msg = update.get("message")
            if not msg:
                continue
            
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "").strip()
            
            # ONLY respond to owner
            if chat_id != OWNER:
                print(f"Ignored: {chat_id}")
                continue
            
            # ONE response per message
            print(f"You: {text}")
            
            if text == "/start":
                api("sendMessage", {"chat_id": chat_id, "text": "🏦 Wyllene ATM ready.\n/login | /balance"})
            elif text == "/login":
                api("sendMessage", {"chat_id": chat_id, "text": "Username?"})
            elif text == "/balance":
                r = server_cmd({"cmd": "BALANCE"})
                api("sendMessage", {"chat_id": chat_id, "text": f"💰 ${r.get('balance',0):,.2f}"})
            else:
                api("sendMessage", {"chat_id": chat_id, "text": f"OK: {text}"})
        
        time.sleep(0.3)
    
    except KeyboardInterrupt:
        print("Stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(2)
