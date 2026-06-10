#!/usr/bin/env python3

import json
import os
import socket
import threading
from datetime import datetime
# from cryptography.fernet import Fernet

# ---------- Configuration ----------
HOST = '0.0.0.0'  # Listen on all interfaces (use '127.0.0.1' for local only)
PORT = 9999
ENCRYPTED_FILE = "accounts.json"
ACCOUNTS_FILE = "accounts.json"
ENCRYPTION_KEY = b'Y7qDBDOr-1lSSHY12tnq46oLQv23vg08GvV8V8Fr4MY='  # Replace with actual key from client

# ---------- Data Handling ----------
def get_cipher():
    return Fernet(ENCRYPTION_KEY)

def load_accounts():
    cipher = None
    if os.path.exists(ENCRYPTED_FILE):
        with open(ENCRYPTED_FILE, 'rb') as f:
            encrypted = f.read()
        decrypted = cipher.decrypt(encrypted)
        return json.loads(decrypted.decode())
    elif os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, 'r') as f:
            data = json.load(f)
        save_accounts(data)
        return data
    else:
        accounts = {
            "wyllene": {
                "pin": "1234",
                "balance": 1000.0,
                "transactions": []
            }
        }
        save_accounts(accounts)
        return accounts

def save_accounts(accounts):
    cipher = None
    json_data = json.dumps(accounts, indent=4).encode()
    encrypted = cipher.encrypt(json_data)
    with open(ENCRYPTED_FILE, 'wb') as f:
        f.write(encrypted)
    if os.path.exists(ACCOUNTS_FILE):
        os.remove(ACCOUNTS_FILE)

def record_transaction(accounts, username, trans_type, amount):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_data = accounts[username]
    if "transactions" not in user_data:
        user_data["transactions"] = []
    user_data["transactions"].append({
        "type": trans_type,
        "amount": amount,
        "time": timestamp
    })
    if len(user_data["transactions"]) > 20:
        user_data["transactions"] = user_data["transactions"][-20:]

# ---------- Request Handling ----------
def handle_client(conn, addr):
    print(f"[+] New connection from {addr}")
    accounts = load_accounts()
    username = None
    authenticated = False

    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            try:
                request = json.loads(data.decode())
            except:
                response = {"status": "error", "message": "Invalid JSON"}
                conn.sendall(json.dumps(response).encode())
                continue

            cmd = request.get("cmd")
            response = {"status": "error", "message": "Unknown command"}

            if cmd == "LOGIN":
                uname = request.get("username")
                pin = request.get("pin")
                if uname == "admin" and pin == "admin123":
                    authenticated = True
                    username = "admin"
                    response = {"status": "ok", "admin": True}
                elif uname in accounts and accounts[uname]["pin"] == pin:
                    authenticated = True
                    username = uname
                    response = {"status": "ok", "balance": accounts[uname]["balance"]}
                else:
                    response = {"status": "error", "message": "Invalid credentials"}

            elif not authenticated:
                response = {"status": "error", "message": "Not authenticated"}

            elif cmd == "BALANCE":
                response = {"status": "ok", "balance": accounts[username]["balance"]}

            elif cmd == "DEPOSIT":
                amount = request.get("amount")
                try:
                    amount = float(amount)
                    if amount <= 0:
                        raise ValueError
                    accounts[username]["balance"] += amount
                    record_transaction(accounts, username, "DEPOSIT", amount)
                    save_accounts(accounts)
                    response = {"status": "ok", "new_balance": accounts[username]["balance"]}
                except:
                    response = {"status": "error", "message": "Invalid amount"}

            elif cmd == "WITHDRAW":
                amount = request.get("amount")
                try:
                    amount = float(amount)
                    if amount <= 0 or amount > accounts[username]["balance"]:
                        raise ValueError
                    accounts[username]["balance"] -= amount
                    record_transaction(accounts, username, "WITHDRAW", amount)
                    save_accounts(accounts)
                    response = {"status": "ok", "new_balance": accounts[username]["balance"]}
                except:
                    response = {"status": "error", "message": "Invalid amount or insufficient funds"}

            elif cmd == "HISTORY":
                trans = accounts[username].get("transactions", [])
                response = {"status": "ok", "history": trans}

            elif cmd == "CHANGE_PIN":
                old = request.get("old_pin")
                new = request.get("new_pin")
                if accounts[username]["pin"] != old:
                    response = {"status": "error", "message": "Incorrect current PIN"}
                elif not (new.isdigit() and len(new) == 4):
                    response = {"status": "error", "message": "New PIN must be 4 digits"}
                else:
                    accounts[username]["pin"] = new
                    save_accounts(accounts)
                    response = {"status": "ok"}

            elif cmd == "ADMIN_VIEW_ALL":
                if username != "admin":
                    response = {"status": "error", "message": "Admin only"}
                else:
                    summary = {u: {"balance": data["balance"]} for u, data in accounts.items()}
                    response = {"status": "ok", "accounts": summary, "total": sum(d["balance"] for d in accounts.values())}

            elif cmd == "ADMIN_RESET_PIN":
                if username != "admin":
                    response = {"status": "error", "message": "Admin only"}
                else:
                    target = request.get("target_user")
                    new_pin = request.get("new_pin")
                    if target not in accounts:
                        response = {"status": "error", "message": "User not found"}
                    elif not (new_pin.isdigit() and len(new_pin) == 4):
                        response = {"status": "error", "message": "PIN must be 4 digits"}
                    else:
                        accounts[target]["pin"] = new_pin
                        save_accounts(accounts)
                        response = {"status": "ok"}

            elif cmd == "QUIT":
                break

            conn.sendall(json.dumps(response).encode())

    except Exception as e:
        print(f"[!] Error with {addr}: {e}")
    finally:
        conn.close()
        print(f"[-] Connection closed from {addr}")

# ---------- Main Server Loop ----------
def main():
    print("🏦 WYLLENE ATM SERVER STARTING...")
    print(f"Listening on {HOST}:{PORT}")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print("Server ready. Waiting for connections...")
    try:
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\nShutting down server.")
    finally:
        server.close()

if __name__ == "__main__":
    main()
