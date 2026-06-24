"""Telegram Bot for Wyllene ATM."""
import requests
import json
import socket
import time
from config import BOT_TOKEN, HOST, SOCKET_PORT
from database import get_user

class WylleneBot:
    def __init__(self):
        # Only these users can use the bot (add your Telegram user ID)
        self.allowed_users = [6819329002]  # Set to None to allow everyone, or a list like [123456789]
        self.blocked_terms = ["ads", "promo", "free money", "click here", "http", ".com"]
        self.token = BOT_TOKEN
        self.host = HOST
        self.port = SOCKET_PORT
        self.sessions = {}  # chat_id -> {"username":..., "step":...}
    
    def send_to_server(self, command):
        """Send command to socket server."""
        try:
            s = socket.socket()
            s.settimeout(5)
            s.connect((self.host, self.port))
            s.sendall(json.dumps(command).encode())
            response = json.loads(s.recv(8192).decode())
            s.close()
            return response
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def send_message(self, chat_id, text):
        """Send message to Telegram chat."""
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        requests.post(url, json=payload)
    
    def handle_login(self, chat_id, text):
        """Handle multi-step login flow."""
        session = self.sessions.get(chat_id, {})
        step = session.get("step", "")
        
        if step == "username":
            session["username"] = text.strip().lower()
            session["step"] = "pin"
            self.sessions[chat_id] = session
            self.send_message(chat_id, "🔐 Enter your PIN:")
        
        elif step == "pin":
            session["pin"] = text.strip()
            session["step"] = "security"
            self.sessions[chat_id] = session
            self.send_message(chat_id, "🔑 Security answer:")
        
        elif step == "security":
            username = session["username"]
            pin = session["pin"]
            answer = text.strip().lower()
            
            response = self.send_to_server({
                "cmd": "LOGIN",
                "username": username,
                "pin": pin,
                "security_answer": answer
            })
            
            if response.get("status") == "ok":
                role = response.get("role", "employee")
                balance = response.get("balance", 0)
                emoji = {"ceo": "👑", "manager": "⭐"}.get(role, "👤")
                
                self.send_message(chat_id,
                    f"{emoji} <b>Welcome, {username}!</b>\n"
                    f"Role: {role.upper()}\n"
                    f"Balance: ${balance:,.2f}\n\n"
                    f"Type /menu for commands.")
                
                self.sessions[chat_id] = {"username": username, "role": role, "logged_in": True}
                self.send_to_server({"cmd": "SET_CHAT_ID", "chat_id": str(chat_id)})
            else:
                self.send_message(chat_id, f"❌ {response.get('message', 'Login failed')}")
            
            # Clear login state
            if chat_id in self.sessions:
                self.sessions[chat_id].pop("step", None)
    
    def handle_command(self, chat_id, command):
        # Check if user is allowed
        if self.allowed_users and chat_id not in self.allowed_users:
            self.send_message(chat_id, "⛔ Access denied. This is a private bot.")
            return
        
        # Check for spam keywords
        text_lower = command.lower()
        for term in self.blocked_terms:
            if term in text_lower:
                print(f"🚫 Blocked spam from {chat_id}: {command}")
                return  # Silently ignore spam
        """Handle bot commands."""
        session = self.sessions.get(chat_id, {})
        text = command.strip().lower()
        parts = text.split()
        cmd = parts[0]
        
        # Login flow
        if cmd == "/login":
            self.sessions[chat_id] = {"step": "username"}
            self.send_message(chat_id, "👤 Enter your username:")
            return
        
        # Handle login steps
        if session.get("step"):
            self.handle_login(chat_id, command)
            return
        
        # Check if logged in
        if not session.get("logged_in"):
            self.send_message(chat_id, "Please /login first.")
            return
        
        # ========== COMMANDS ==========
        username = session["username"]
        
        if cmd == "/start" or cmd == "/menu":
            role = session.get("role", "employee")
            menu = "<b>🏢 Wyllene Enterprise Bank</b>\n\n"
            menu += "<b>Banking:</b>\n"
            menu += "/balance - Check balance\n"
            menu += "/deposit &lt;amount&gt;\n"
            menu += "/withdraw &lt;amount&gt;\n"
            menu += "/transfer &lt;user&gt; &lt;amount&gt;\n"
            menu += "/history - Recent transactions\n"
            
            if role in ("ceo", "manager"):
                menu += "\n<b>Management:</b>\n"
                menu += "/employees - List all employees\n"
            
            if role == "ceo":
                menu += "\n<b>CEO Tools:</b>\n"
                menu += "/payroll - Process salaries\n"
                menu += "/audit - View audit log\n"
                menu += "/ceo - CEO link menu\n"
                menu += "/apikey - Generate API key\n"
            
            self.send_message(chat_id, menu)
        
        elif cmd == "/balance":
            resp = self.send_to_server({"cmd": "BALANCE"})
            self.send_message(chat_id, f"💰 Balance: ${resp.get('balance', 0):,.2f}")
        
        elif cmd == "/deposit":
            if len(parts) < 2:
                self.send_message(chat_id, "Usage: /deposit &lt;amount&gt;")
            else:
                try:
                    amount = float(parts[1])
                    resp = self.send_to_server({"cmd": "DEPOSIT", "amount": amount})
                    if resp.get("status") == "ok":
                        self.send_message(chat_id, f"✅ Deposited ${amount:,.2f}\nNew balance: ${resp['new_balance']:,.2f}")
                    else:
                        self.send_message(chat_id, f"❌ {resp.get('message')}")
                except ValueError:
                    self.send_message(chat_id, "❌ Invalid amount")
        
        elif cmd == "/withdraw":
            if len(parts) < 2:
                self.send_message(chat_id, "Usage: /withdraw &lt;amount&gt;")
            else:
                try:
                    amount = float(parts[1])
                    resp = self.send_to_server({"cmd": "WITHDRAW", "amount": amount})
                    if resp.get("status") == "ok":
                        self.send_message(chat_id, f"✅ Withdrew ${amount:,.2f}\nNew balance: ${resp['new_balance']:,.2f}")
                    elif resp.get("status") == "pending_approval":
                        self.send_message(chat_id, f"⏳ {resp.get('message')}")
                    else:
                        self.send_message(chat_id, f"❌ {resp.get('message')}")
                except ValueError:
                    self.send_message(chat_id, "❌ Invalid amount")
        
        elif cmd == "/transfer":
            if len(parts) < 3:
                self.send_message(chat_id, "Usage: /transfer &lt;username&gt; &lt;amount&gt;")
            else:
                try:
                    target = parts[1]
                    amount = float(parts[2])
                    resp = self.send_to_server({"cmd": "TRANSFER", "recipient": target, "amount": amount})
                    if resp.get("status") == "ok":
                        self.send_message(chat_id, f"✅ Transferred ${amount:,.2f} to {target}")
                    else:
                        self.send_message(chat_id, f"❌ {resp.get('message')}")
                except ValueError:
                    self.send_message(chat_id, "❌ Invalid amount")
        
        elif cmd == "/history":
            resp = self.send_to_server({"cmd": "HISTORY"})
            if resp.get("status") == "ok":
                history = resp.get("history", [])
                if history:
                    lines = [f"{t['timestamp']} {t['type']}: ${t['amount']:,.2f}" for t in history[:5]]
                    self.send_message(chat_id, "📋 <b>Recent transactions:</b>\n" + "\n".join(lines))
                else:
                    self.send_message(chat_id, "No transactions yet.")
        
        elif cmd == "/employees":
            resp = self.send_to_server({"cmd": "LIST_EMPLOYEES"})
            if resp.get("status") == "ok":
                emps = resp.get("employees", [])
                if emps:
                    lines = [f"{e['username']} - {e['role'].upper()} - {e['department']} - ${e['balance']:,.2f}" for e in emps]
                    self.send_message(chat_id, "👥 <b>Employees:</b>\n" + "\n".join(lines))
                else:
                    self.send_message(chat_id, "No employees found.")
        
        elif cmd == "/payroll":
            resp = self.send_to_server({"cmd": "PROCESS_PAYROLL"})
            if resp.get("status") == "ok":
                self.send_message(chat_id, "✅ Payroll processed!\n" + "\n".join(resp.get("processed", [])))
            else:
                self.send_message(chat_id, f"❌ {resp.get('message')}")
        
        elif cmd == "/audit":
            resp = self.send_to_server({"cmd": "VIEW_AUDIT_LOG"})
            if resp.get("status") == "ok":
                logs = resp.get("logs", [])
                if logs:
                    lines = [f"{l['timestamp']} {l['username']}: {l['action']} - {l['details']}" for l in logs[:10]]
                    self.send_message(chat_id, "📋 <b>Audit Log:</b>\n" + "\n".join(lines))
                else:
                    self.send_message(chat_id, "No audit entries.")
        
        elif cmd == "/apikey":
            resp = self.send_to_server({"cmd": "GENERATE_API_KEY"})
            if resp.get("status") == "ok":
                self.send_message(chat_id, f"🔑 <b>API Key:</b>\n<code>{resp['api_key']}</code>")
        
        elif cmd == "/ceo":
            self.send_message(chat_id,
                "🔗 <b>CEO Link Menu:</b>\n"
                "/ceo_generate &lt;employee&gt; - Create link token\n"
                "/ceo_employees - List linked employees\n"
                "/ceo_revoke &lt;employee&gt; - Revoke link")
        
        elif cmd == "/ceo_generate":
            if len(parts) < 2:
                self.send_message(chat_id, "Usage: /ceo_generate &lt;employee&gt;")
            else:
                resp = self.send_to_server({"cmd": "GENERATE_LINK_TOKEN", "employee": parts[1]})
                if resp.get("status") == "ok":
                    self.send_message(chat_id, f"🔗 Token: <code>{resp['token']}</code>\nShare with {parts[1]} to use /link {resp['token']}")
                else:
                    self.send_message(chat_id, f"❌ {resp.get('message')}")
        
        elif cmd == "/link":
            if len(parts) < 2:
                self.send_message(chat_id, "Usage: /link &lt;token&gt;")
            else:
                resp = self.send_to_server({"cmd": "LINK_ACCOUNT", "token": parts[1]})
                self.send_message(chat_id, f"{'✅' if resp.get('status')=='ok' else '❌'} {resp.get('message','')}")
        
        else:
            self.send_message(chat_id, "Unknown command. Type /menu for options.")
    
    def run(self):
        """Main polling loop."""
        # Wait for server
        print("⏳ Waiting for server...")
        for i in range(15):
            try:
                s = socket.socket()
                s.settimeout(3)
                s.connect((self.host, self.port))
                s.close()
                print("✅ Server connected")
                break
            except:
                time.sleep(3)
        
        offset = 0
        print("🤖 Enterprise Bot started.")
        
        while True:
            try:
                url = f"https://api.telegram.org/bot{self.token}/getUpdates"
                resp = requests.get(url, params={"offset": offset, "timeout": 30})
                data = resp.json()
                
                if data.get("ok"):
                    for update in data["result"]:
                        offset = update["update_id"] + 1
                        if "message" in update and "text" in update["message"]:
                            chat_id = update["message"]["chat"]["id"]
                            text = update["message"]["text"].strip()
                            print(f"📩 {chat_id}: {text}")
                            self.handle_command(chat_id, text)
            except Exception as e:
                print(f"Poll error: {e}")
            time.sleep(0.5)

if __name__ == "__main__":
    bot = WylleneBot()
    bot.run()
