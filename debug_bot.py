

import requests, json, socket, time, threading

TOKEN = "8980273422:AAG7c84_OTsFSXnWGLzF-2nSGd8mOfrS0eA"
HOST = 'localhost'
PORT = 9999

def send_cmd(cmd_dict):
    try:
        s = socket.socket()
        s.settimeout(5)
        s.connect((HOST, PORT))
        s.sendall(json.dumps(cmd_dict).encode())
        resp = s.recv(4096).decode()
        s.close()
        return json.loads(resp)
    except Exception as e:
        print("SERVER ERROR:", e)
        return {"status":"error","message":str(e)}

def process_message(chat_id, text):
    print(f"\n>>> Received from {chat_id}: {text}")
    parts = text.split()
    cmd = parts[0].lower() if parts else ''
    reply = "I don't understand. Try /start"

    if cmd == '/start':
        reply = "Welcome to Wyllene ATM!\n/login user pin security_answer\n/balance\n/deposit amount\n/withdraw amount"
    elif cmd == '/login' and len(parts) >= 4:
        resp = send_cmd({"cmd":"LOGIN","username":parts[1],"pin":parts[2],"security_answer":parts[3]})
        print("Server response:", resp)
        if resp.get('status') == 'ok':
            if resp.get('admin'):
                reply = "Logged in as admin."
            else:
                reply = f"Logged in. Balance: ${resp['balance']:.2f}"
        else:
            reply = f"Login failed: {resp.get('message','')}"
    elif cmd == '/balance':
        resp = send_cmd({"cmd":"BALANCE"})
        print("Server response:", resp)
        if resp.get('status') == 'ok':
            reply = f"Balance: ${resp['balance']:.2f}"
        else:
            reply = f"Error: {resp.get('message','')}"
    elif cmd == '/deposit' and len(parts) >= 2:
        try:
            amt = float(parts[1])
            resp = send_cmd({"cmd":"DEPOSIT","amount":amt})
            print("Server response:", resp)
            if resp.get('status') == 'ok':
                reply = f"Deposited ${amt:.2f}. New balance: ${resp['new_balance']:.2f}"
            else:
                reply = f"Error: {resp.get('message','')}"
        except ValueError:
            reply = "Invalid amount."
    elif cmd == '/withdraw' and len(parts) >= 2:
        try:
            amt = float(parts[1])
            resp = send_cmd({"cmd":"WITHDRAW","amount":amt})
            print("Server response:", resp)
            if resp.get('status') == 'ok':
                reply = f"Withdrew ${amt:.2f}. New balance: ${resp['new_balance']:.2f}"
            else:
                reply = f"Error: {resp.get('message','')}"
        except ValueError:
            reply = "Invalid amount."

    # Send reply back to Telegram
    print(f"<<< Sending to {chat_id}: {reply}")
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    resp = requests.post(url, json={"chat_id": chat_id, "text": reply})
    print("Telegram response:", resp.json())

def poll():
    offset = 0
    print("🤖 Debug bot polling... Send /start to @wylleneATM_bot")
    while True:
        try:
            resp = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", params={"offset": offset, "timeout": 30})
            data = resp.json()
            if data.get('ok'):
                for upd in data['result']:
                    offset = upd['update_id'] + 1
                    msg = upd.get('message')
                    if msg and 'text' in msg:
                        threading.Thread(target=process_message, args=(msg['chat']['id'], msg['text'])).start()
            else:
                print("getUpdates error:", data)
        except requests.exceptions.ReadTimeout:
            pass
        except Exception as e:
            print("Poll error:", e)
        time.sleep(0.5)

if __name__ == "__main__":
    poll()
