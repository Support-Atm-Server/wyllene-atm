import requests, json, socket, time, os

TOKEN = os.environ.get("BOT_TOKEN", "8980273422:AAG7c84_OTsFSXnWGLzF-2nSGd8mOfrS0eA")
HOST = os.environ.get("SERVER_HOST", "localhost")
PORT = int(os.environ.get("SERVER_PORT", "9999"))

def server(cmd):
    try:
        s = socket.socket(); s.settimeout(5)
        s.connect((HOST, PORT)); s.sendall(json.dumps(cmd).encode())
        r = json.loads(s.recv(4096).decode()); s.close()
        return r
    except Exception as e:
        return {"status":"error","message":str(e)}

def send(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

state = {}; user = {}

def process_text(chat_id, text):
    s = state.get(chat_id); text = text.strip().lower()
    if s == "LOGIN_USER": user[chat_id] = {"username":text}; state[chat_id]="LOGIN_PIN"; send(chat_id,"PIN:"); return
    if s == "LOGIN_PIN": user[chat_id]["pin"]=text; state[chat_id]="LOGIN_SEC"; send(chat_id,"Security answer:"); return
    if s == "LOGIN_SEC":
        u=user[chat_id]["username"]; p=user[chat_id]["pin"]; a=text
        r=server({"cmd":"LOGIN","username":u,"pin":p,"security_answer":a})
        if r.get("status")=="ok":
            user[chat_id]={"username":u,"logged_in":True}
            send(chat_id, f"✅ Logged in as {u}. Balance: ${r['balance']:.2f}")
            server({"cmd":"SET_CHAT_ID","chat_id":chat_id})
        else: send(chat_id, f"❌ {r.get('message','')}")
        state.pop(chat_id,None); return
    # Default
    if text=="/start":
        if user.get(chat_id,{}).get("logged_in"):
            send(chat_id, "You are already logged in.")
        else:
            send(chat_id, "Welcome! Type /login to start.")
    elif text=="/login":
        state[chat_id]="LOGIN_USER"; send(chat_id,"Username:")
    else:
        send(chat_id,"Commands: /start, /login")

def main():
    offset=0; print("🤖 Bot started (simple mode).")
    while True:
        try:
            resp = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", params={"offset":offset,"timeout":30})
            data = resp.json()
            if data.get("ok"):
                for upd in data["result"]:
                    offset = upd["update_id"]+1
                    if "message" in upd and "text" in upd["message"]:
                        process_text(upd["message"]["chat"]["id"], upd["message"]["text"])
        except Exception as e: print("Poll error:", e)
        time.sleep(0.5)

if __name__=="__main__":
    main()
