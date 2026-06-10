import requests, json, socket, time, threading

TOKEN = "8980273422:AAG7c84_OTsFSXnWGLzF-2nSGd8mOfrS0eA"
HOST = "localhost"
PORT = 9999

# Simple in-memory session: chat_id -> {"username": ..., "logged_in": bool}
sessions = {}

# -------- Server communication ----------
def send_to_server(cmd_dict):
    try:
        s = socket.socket()
        s.settimeout(5)
        s.connect((HOST, PORT))
        s.sendall(json.dumps(cmd_dict).encode())
        resp = json.loads(s.recv(4096).decode())
        s.close()
        return resp
    except Exception as e:
        print("Server error:", e)
        return {"status":"error","message":str(e)}

# -------- Inline keyboard --------
def main_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "💰 Balance", "callback_data": "/balance"},
             {"text": "💸 Deposit", "callback_data": "/deposit"}],
            [{"text": "🏧 Withdraw", "callback_data": "/withdraw"},
             {"text": "📋 Statement", "callback_data": "/history"}],
            [{"text": "🔐 Change PIN", "callback_data": "/changepin"}],
            [{"text": "❌ Logout", "callback_data": "/logout"}]
        ]
    }

def start_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🔑 Login", "callback_data": "/login"}]
        ]
    }

# -------- Message handler --------
def handle_message(chat_id, text):
    # If it's a callback query (inline button), we'll handle separately
    pass  # this bot does not use callback queries directly yet, just text

def process_command(chat_id, cmd, args=[]):
    reply = ""
    markup = None
    session = sessions.get(chat_id, {})

    if cmd == "/start":
        if session.get("logged_in"):
            reply = f"Welcome back, {session['username']}! Choose an action:"
            markup = main_menu_keyboard()
        else:
            reply = "Welcome to Wyllene ATM!\nPlease /login to access your account."
            markup = start_keyboard()

    elif cmd == "/login":
        if len(args) < 3:
            reply = "Usage: /login <username> <pin> <security_answer>"
        else:
            username, pin, security = args[0], args[1], args[2]
            resp = send_to_server({"cmd":"LOGIN","username":username,"pin":pin,"security_answer":security})
            if resp.get("status") == "ok":
                sessions[chat_id] = {"username": username, "logged_in": True}
                if resp.get("admin"):
                    reply = "Logged in as admin."
                else:
                    reply = f"Logged in as {username}.\nBalance: ${resp['balance']:.2f}"
                markup = main_menu_keyboard()
            else:
                reply = f"Login failed: {resp.get('message','')}"

    elif cmd == "/balance":
        if not session.get("logged_in"):
            reply = "You're not logged in. Use /login first."
        else:
            resp = send_to_server({"cmd":"BALANCE"})
            if resp.get("status") == "ok":
                reply = f"Balance: ${resp['balance']:.2f}"
            else:
                reply = f"Error: {resp.get('message','')}"

    elif cmd == "/deposit":
        if not session.get("logged_in"):
            reply = "Please login first."
        elif not args:
            reply = "Please specify amount: /deposit 100"
        else:
            try:
                amt = float(args[0])
                resp = send_to_server({"cmd":"DEPOSIT","amount":amt})
                if resp.get("status") == "ok":
                    reply = f"Deposited ${amt:.2f}\nNew balance: ${resp['new_balance']:.2f}"
                else:
                    reply = f"Error: {resp.get('message','')}"
            except ValueError:
                reply = "Invalid amount."

    elif cmd == "/withdraw":
        if not session.get("logged_in"):
            reply = "Please login first."
        elif not args:
            reply = "Usage: /withdraw 50"
        else:
            try:
                amt = float(args[0])
                resp = send_to_server({"cmd":"WITHDRAW","amount":amt})
                if resp.get("status") == "ok":
                    reply = f"Withdrew ${amt:.2f}\nNew balance: ${resp['new_balance']:.2f}"
                else:
                    reply = f"Error: {resp.get('message','')}"
            except ValueError:
                reply = "Invalid amount."

    elif cmd == "/history":
        if not session.get("logged_in"):
            reply = "Please login first."
        else:
            resp = send_to_server({"cmd":"HISTORY"})
            if resp.get("status") == "ok":
                hist = resp.get("history", [])
                if hist:
                    lines = [f"{t['time']} {t['type']} ${t['amount']:.2f}" for t in hist[:5]]
                    reply = "Last transactions:\n" + "\n".join(lines)
                else:
                    reply = "No transactions yet."
            else:
                reply = "Error fetching history."

    elif cmd == "/changepin":
        if not session.get("logged_in"):
            reply = "Please login first."
        elif len(args) < 2:
            reply = "Usage: /changepin <old_pin> <new_pin>"
        else:
            old, new = args[0], args[1]
            resp = send_to_server({"cmd":"CHANGE_PIN","old_pin":old,"new_pin":new})
            if resp.get("status") == "ok":
                reply = "PIN changed successfully."
            else:
                reply = f"Error: {resp.get('message','')}"

    elif cmd == "/logout":
        if chat_id in sessions:
            del sessions[chat_id]
        reply = "Logged out."
        markup = start_keyboard()

    else:
        reply = "Unknown command. Try /start"

    # Send reply
    send_message(chat_id, reply, markup)

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    r = requests.post(url, json=payload)
    print("Sent:", r.json())

# -------- Polling loop --------
def main():
    offset = 0
    print("🤖 Enhanced Wyllene ATM bot is running...")
    while True:
        try:
            resp = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates",
                                params={"offset": offset, "timeout": 30})
            data = resp.json()
            if data.get("ok"):
                for upd in data["result"]:
                    offset = upd["update_id"] + 1
                    msg = upd.get("message")
                    if msg and "text" in msg:
                        text = msg["text"].strip()
                        chat_id = msg["chat"]["id"]
                        parts = text.split()
                        cmd = parts[0].lower()
                        args = parts[1:] if len(parts) > 1 else []
                        print(f"Received: {text}")
                        process_command(chat_id, cmd, args)
        except Exception as e:
            print("Poll error:", e)
        time.sleep(0.5)

if __name__ == "__main__":
    main()
