import requests, json, socket, time, os

TOKEN = os.environ.get("BOT_TOKEN", "8980273422:AAG7c84_OTsFSXnWGLzF-2nSGd8mOfrS0eA")
HOST = os.environ.get("SERVER_HOST", "localhost")
PORT = int(os.environ.get("SERVER_PORT", "9999"))

def server(cmd):
    try:
        s = socket.socket(); s.settimeout(5)
        s.connect((HOST, PORT)); s.sendall(json.dumps(cmd).encode())
        r = json.loads(s.recv(8192).decode()); s.close()
        return r
    except Exception as e:
        return {"status":"error","message":str(e)}

def send(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})

state = {}; user = {}

def process_text(chat_id, text):
    s = state.get(chat_id); text = text.strip().lower()
    
    # Login flow
    if s == "LOGIN_USER": user[chat_id]={"username":text}; state[chat_id]="LOGIN_PIN"; send(chat_id,"🔐 PIN:"); return
    if s == "LOGIN_PIN": user[chat_id]["pin"]=text; state[chat_id]="LOGIN_SEC"; send(chat_id,"🔑 Security answer:"); return
    if s == "LOGIN_SEC":
        u=user[chat_id]["username"]; p=user[chat_id]["pin"]; a=text
        r=server({"cmd":"LOGIN","username":u,"pin":p,"security_answer":a})
        if r.get("status")=="ok":
            user[chat_id]={"username":u,"role":r['role'],"logged_in":True}
            role_emoji = "👑" if r['role']=='ceo' else "⭐" if r['role']=='manager' else "👤"
            send(chat_id, f"{role_emoji} <b>{u}</b> logged in as <b>{r['role'].upper()}</b>\n💼 {r.get('department','')}\n💰 Balance: ${r['balance']:,.2f}")
            server({"cmd":"SET_CHAT_ID","chat_id":chat_id})
        else: send(chat_id, f"❌ {r.get('message','')}")
        state.pop(chat_id,None); return
    
    # Commands
    if text=="/start":
        if user.get(chat_id,{}).get("logged_in"):
            send(chat_id, "🏢 <b>Wyllene Enterprise Bank</b>\n\nCommands:\n/balance - Check balance\n/deposit <amount>\n/withdraw <amount>\n/transfer <user> <amount>\n/employees - List employees (manager+)\n/payroll - Process salaries (CEO)\n/audit - View audit log (CEO)\n/ceo - CEO link menu\n/apikey - Generate API key")
        else:
            send(chat_id, "🏢 <b>Wyllene Enterprise Bank</b>\nWelcome! Please /login to access your account.")
    elif text=="/login":
        state[chat_id]="LOGIN_USER"; send(chat_id,"👤 Username:")
    elif text=="/balance":
        r=server({"cmd":"BALANCE"})
        send(chat_id, f"💰 Balance: ${r.get('balance',0):,.2f}")
    elif text.startswith("/deposit"):
        parts=text.split()
        if len(parts)<2: send(chat_id,"Usage: /deposit <amount>")
        else:
            r=server({"cmd":"DEPOSIT","amount":float(parts[1])})
            send(chat_id, f"{'✅' if r.get('status')=='ok' else '❌'} {r.get('message','')}\nNew balance: ${r.get('new_balance',0):,.2f}" if r.get('new_balance') else "")
    elif text.startswith("/withdraw"):
        parts=text.split()
        if len(parts)<2: send(chat_id,"Usage: /withdraw <amount>")
        else:
            r=server({"cmd":"WITHDRAW","amount":float(parts[1])})
            if r.get('status')=='pending_approval': send(chat_id, f"⏳ {r.get('message','')}")
            else: send(chat_id, f"{'✅' if r.get('status')=='ok' else '❌'} New balance: ${r.get('new_balance',0):,.2f}" if r.get('new_balance') else "")
    elif text.startswith("/transfer"):
        parts=text.split()
        if len(parts)<3: send(chat_id,"Usage: /transfer <username> <amount>")
        else:
            r=server({"cmd":"TRANSFER","recipient":parts[1],"amount":float(parts[2])})
            send(chat_id, f"{'✅' if r.get('status')=='ok' else '❌'} {r.get('message','')}")
    elif text=="/employees":
        r=server({"cmd":"LIST_EMPLOYEES"})
        if r.get('status')=='ok':
            emps=r.get('employees',[])
            lines=[f"{e['username']} - {e['role'].upper()} - {e['department']} - ${e['balance']:,.2f}" for e in emps]
            send(chat_id, "👥 <b>Employees:</b>\n"+"\n".join(lines))
        else: send(chat_id, f"❌ {r.get('message','')}")
    elif text=="/payroll":
        r=server({"cmd":"PROCESS_PAYROLL"})
        if r.get('status')=='ok': send(chat_id, "✅ Payroll processed!\n"+"\n".join(r.get('processed',[])))
        else: send(chat_id, f"❌ {r.get('message','')}")
    elif text=="/audit":
        r=server({"cmd":"VIEW_AUDIT_LOG"})
        if r.get('status')=='ok':
            logs=r.get('logs',[])
            lines=[f"{l['timestamp']} {l['username']}: {l['action']} - {l['details']}" for l in logs[:10]]
            send(chat_id, "📋 <b>Audit Log:</b>\n"+"\n".join(lines))
        else: send(chat_id, f"❌ {r.get('message','')}")
    elif text=="/apikey":
        r=server({"cmd":"GENERATE_API_KEY"})
        if r.get('status')=='ok': send(chat_id, f"🔑 API Key: <code>{r['api_key']}</code>")
        else: send(chat_id, f"❌ {r.get('message','')}")
    elif text=="/ceo":
        send(chat_id, "🔗 <b>CEO Link Menu:</b>\n/ceo_generate <employee> - Create link token\n/ceo_employees - List linked\n/ceo_revoke <employee> - Revoke link")
    elif text.startswith("/ceo_generate"):
        parts=text.split()
        if len(parts)<2: send(chat_id,"Usage: /ceo_generate <employee>")
        else:
            r=server({"cmd":"GENERATE_LINK_TOKEN","employee":parts[1]})
            if r.get('status')=='ok': send(chat_id, f"🔗 Token: <code>{r['token']}</code>\nGive to {parts[1]} to link with /link {r['token']}")
            else: send(chat_id, f"❌ {r.get('message','')}")
    elif text.startswith("/link"):
        parts=text.split()
        if len(parts)<2: send(chat_id,"Usage: /link <token>")
        else:
            r=server({"cmd":"LINK_ACCOUNT","token":parts[1]})
            if r.get('status')=='ok': send(chat_id, f"✅ {r.get('message','')}")
            else: send(chat_id, f"❌ {r.get('message','')}")
    else:
        send(chat_id, "Unknown command. Type /start for menu.")

def main():
    # Wait for server
    for i in range(15):
        try:
            s=socket.socket(); s.settimeout(3); s.connect((HOST,PORT)); s.close()
            break
        except: time.sleep(3)
    
    offset=0; print("🏢 Enterprise Bot started.")
    while True:
        try:
            resp=requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", params={"offset":offset,"timeout":30})
            data=resp.json()
            if data.get("ok"):
                for upd in data["result"]:
                    offset=upd["update_id"]+1
                    if "message" in upd and "text" in upd["message"]:
                        process_text(upd["message"]["chat"]["id"], upd["message"]["text"])
        except Exception as e: print("Poll error:", e)
        time.sleep(0.5)

if __name__=="__main__":
    main()
