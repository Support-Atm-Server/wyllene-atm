import json, os, sys, socket, threading, subprocess, csv
from datetime import datetime
import curses
from colorama import init, Fore, Style
init(autoreset=True)

# Sound
try:
    from playsound import playsound
    SOUND = True
except:
    SOUND = False
    def playsound(f, block=False): print('\a',end='',flush=True)

# Chart
try:
    import matplotlib.pyplot as plt
    CHART = True
except:
    CHART = False

# Network
class NetworkClient:
    def __init__(self, host='localhost', port=9999):
        self.host = host; self.port = port; self.sock = None
    def connect(self):
        self.sock = socket.socket(); self.sock.connect((self.host, self.port))
    def send(self, req):
        self.sock.sendall(json.dumps(req).encode()); return json.loads(self.sock.recv(4096).decode())
    def close(self):
        if self.sock: self.sock.close()
    def login(self, u, p, sec_a=""): return self.send({"cmd":"LOGIN","username":u,"pin":p,"security_answer":sec_a})
    def get_sec_q(self, u): return self.send({"cmd":"GET_SECURITY_QUESTION","username":u})
    def balance(self): return self.send({"cmd":"BALANCE"})
    def deposit(self, a): return self.send({"cmd":"DEPOSIT","amount":a})
    def withdraw(self, a): return self.send({"cmd":"WITHDRAW","amount":a})
    def history(self): return self.send({"cmd":"HISTORY"})
    def change_pin(self, o, n): return self.send({"cmd":"CHANGE_PIN","old_pin":o,"new_pin":n})
    def admin_view(self): return self.send({"cmd":"ADMIN_VIEW_ALL"})
    def admin_reset_pin(self, t, p): return self.send({"cmd":"ADMIN_RESET_PIN","target_user":t,"new_pin":p})

# ---------- TUI ----------
class ATM:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.net = None
        self.username = None
        self.user_data = None
        self.row = 0
        self.menu = ["Check Balance","Deposit","Withdraw","History","Transfer","QR Transfer","AI Assistant","Change PIN","Chart","Export CSV","Register","Set Security Q","Exit"]
        self.admin_menu = ["View All","Reset PIN","Return"]
        self.init_colors()
        self.choose_mode()

    def init_colors(self):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLUE)

    def choose_mode(self):
        self.stdscr.clear()
        self.stdscr.addstr(2,2,"1. Local mode (standalone, JSON)")
        self.stdscr.addstr(3,2,"2. Network mode (connect to server)")
        self.stdscr.addstr(5,2,"Choice: "); self.stdscr.refresh()
        curses.echo(); ch = self.stdscr.getstr(5,10,1).decode(); curses.noecho()
        if ch == '2':
            self.net = NetworkClient()
            self.stdscr.addstr(7,2,"Server IP [localhost]: "); self.stdscr.refresh()
            curses.echo(); ip = self.stdscr.getstr(7,24,20).decode().strip() or "localhost"; curses.noecho()
            self.stdscr.addstr(8,2,"Port [9999]: "); self.stdscr.refresh()
            curses.echo(); port = self.stdscr.getstr(8,13,5).decode().strip() or "9999"; curses.noecho()
            self.net.host = ip; self.net.port = int(port)
            try:
                self.net.connect()
            except:
                self.stdscr.addstr(10,2,"Connection failed! Press any key."); self.stdscr.getch()
                sys.exit(1)
        else:
            # local mode still uses old JSON (for simplicity)
            self.local = True
            # load accounts.json (legacy)
            import json as j
            if os.path.exists("accounts.json"):
                with open("accounts.json") as f: self.accounts = j.load(f)
            else:
                self.accounts = {"wyllene":{"pin":"1234","balance":1000.0,"transactions":[]}}
                with open("accounts.json","w") as f: j.dump(self.accounts,f)
        self.run()

    def login(self):
        self.stdscr.clear()
        self.stdscr.addstr(2,2,"Username: "); self.stdscr.refresh()
        curses.echo(); u = self.stdscr.getstr(2,12,20).decode().strip().lower(); curses.noecho()
        self.stdscr.addstr(3,2,"PIN: "); self.stdscr.refresh()
        curses.echo(); p = self.stdscr.getstr(3,7,4).decode().strip(); curses.noecho()
        if self.net:
            # Get security question first
            resp = self.net.get_sec_q(u)
            if resp.get("status")=="ok":
                q = resp["question"]
                self.stdscr.addstr(5,2,f"Security: {q}"); self.stdscr.refresh()
                curses.echo(); ans = self.stdscr.getstr(6,2,20).decode().strip(); curses.noecho()
                resp = self.net.login(u, p, ans)
            else:
                resp = self.net.login(u, p, "")
            if resp.get("status")=="ok":
                if resp.get("admin"): return "admin"
                self.username = u; self.user_data = {"balance":resp["balance"]}
                return True
        else:
            if u in self.accounts and self.accounts[u]["pin"]==p:
                self.username = u; self.user_data = self.accounts[u]; return True
        self.stdscr.addstr(8,2,"Invalid login. Press any key."); self.stdscr.getch()
        return False

    def run(self):
        while not self.username:
            if not self.login(): continue
        while True:
            self.stdscr.clear()
            self.draw_header()
            options = self.admin_menu if self.username=="admin" else self.menu
            for i,opt in enumerate(options):
                attr = curses.color_pair(4) if i==self.row else curses.A_NORMAL
                self.stdscr.addstr(10+i,4,f"{'▸' if i==self.row else ' '} {opt}", attr)
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if key == curses.KEY_UP: self.row = (self.row-1)%len(options)
            elif key == curses.KEY_DOWN: self.row = (self.row+1)%len(options)
            elif key in [10,13]:
                self.handle(options[self.row])
            elif key == ord('q'): break

    def handle(self, choice):
        if choice == "Check Balance":
            if self.net:
                resp = self.net.balance()
                if resp.get("status")=="ok": self.user_data["balance"] = resp["balance"]
                self.show_msg(f"Balance: ${resp['balance']:.2f}")
            else:
                self.show_msg(f"Balance: ${self.user_data['balance']:.2f}")
        elif choice == "Deposit":
            amt = self.input_dialog("Amount to deposit: $")
            if amt:
                if self.net:
                    resp = self.net.deposit(float(amt))
                    if resp.get("status")=="ok": self.user_data["balance"] = resp["new_balance"]
                    self.show_msg(resp.get("message","Deposit done"))
                else:
                    self.user_data["balance"] += float(amt)
                    self.save_local()
                    self.play_sound("deposit")
                    self.show_msg(f"Deposited ${amt}")
        elif choice == "Withdraw":
            amt = self.input_dialog("Amount to withdraw: $")
            if amt:
                if self.net:
                    resp = self.net.withdraw(float(amt))
                    if resp.get("status")=="ok": self.user_data["balance"] = resp["new_balance"]
                    self.show_msg(resp.get("message","Withdrawn"))
                else:
                    if float(amt) > self.user_data["balance"]: self.show_msg("Insufficient")
                    else:
                        self.user_data["balance"] -= float(amt)
                        self.save_local()
                        self.show_msg(f"Withdrew ${amt}")
        elif choice == "History":
            if self.net:
                resp = self.net.history()
                if resp.get("status")=="ok":
                    self.show_popup("History", resp["history"])
            else:
                trans = self.user_data.get("transactions",[])
                self.show_popup("History", trans)
        elif choice == "Register":
            self.register_user_tui()
        elif choice == "AI Assistant":
            self.ai_assistant()
        elif choice == "QR Transfer":
            self.qr_transfer()
        elif choice == "Transfer":
            self.transfer_money()
        elif choice == "Change PIN":
            old = self.input_dialog("Current PIN: ")
            new = self.input_dialog("New 4-digit PIN: ")
            if old and new and len(new)==4 and new.isdigit():
                if self.net:
                    resp = self.net.change_pin(old, new)
                    self.show_msg(resp.get("message","Done"))
                else:
                    if self.user_data["pin"]==old: self.user_data["pin"]=new; self.save_local(); self.show_msg("PIN changed")
        elif choice == "Chart":
            self.show_chart()
        elif choice == "Export CSV":
            self.export_csv()
        elif choice == "Set Security Q":
            q = self.input_dialog("Question: ")
            a = self.input_dialog("Answer: ")
            if self.net:
                self.net.send({"cmd":"SET_SECURITY","question":q,"answer":a})
                self.show_msg("Security updated")
            else:
                self.show_msg("Only in network mode")
        elif choice == "Exit":
            sys.exit(0)

    
    def register_user_tui(self):
        self.stdscr.clear()
        self.stdscr.addstr(2,2,"--- Register New User ---")
        self.stdscr.addstr(4,2,"Username: "); self.stdscr.refresh()
        curses.echo(); uname = self.stdscr.getstr(4,13,15).decode().strip(); curses.noecho()
        self.stdscr.addstr(5,2,"PIN (4 digits): "); self.stdscr.refresh()
        curses.echo(); pin = self.stdscr.getstr(5,16,4).decode().strip(); curses.noecho()
        self.stdscr.addstr(6,2,"Security question: "); self.stdscr.refresh()
        curses.echo(); q = self.stdscr.getstr(6,22,30).decode().strip(); curses.noecho()
        self.stdscr.addstr(7,2,"Security answer: "); self.stdscr.refresh()
        curses.echo(); a = self.stdscr.getstr(7,19,20).decode().strip(); curses.noecho()
        if not uname or not pin or not q or not a:
            self.show_msg("All fields required."); return
        if self.net:
            resp = self.net.send({"cmd":"REGISTER","username":uname,"pin":pin,"security_q":q,"security_a":a})
            self.show_msg(resp.get("message","Registered"))
        else:
            self.show_msg("Registration only in network mode.")


    def ai_assistant(self):
        self.stdscr.clear()
        self.stdscr.addstr(2,2,"--- AI Assistant ---")
        self.stdscr.addstr(4,2,"Ask me anything (e.g., 'balance', 'deposit 50'): ")
        self.stdscr.refresh()
        curses.echo()
        msg = self.stdscr.getstr(4,50,60).decode().strip()
        curses.noecho()
        if not msg:
            return
        if self.net:
            resp = self.net.send({"cmd":"AI_ASSIST","message":msg})
            if resp.get("status") == "ok":
                self.show_msg(resp.get("reply",""))
            else:
                self.show_msg("AI service unavailable.")
        else:
            self.show_msg("AI only works in network mode.")

    def qr_transfer(self):
        self.stdscr.clear()
        self.stdscr.addstr(2,2,"--- QR Transfer ---")
        self.stdscr.addstr(4,2,"Recipient: "); self.stdscr.refresh()
        curses.echo(); target = self.stdscr.getstr(4,13,15).decode().strip().lower(); curses.noecho()
        self.stdscr.addstr(5,2,"Amount: $"); self.stdscr.refresh()
        curses.echo(); amt_str = self.stdscr.getstr(5,9,10).decode().strip(); curses.noecho()
        try:
            amt = float(amt_str)
            if amt <= 0:
                self.show_msg("Amount must be positive."); return
        except:
            self.show_msg("Invalid amount."); return

        if not self.net:
            self.show_msg("QR transfer only in network mode."); return

        # Generate QR image
        import qrcode, os
        data = json.dumps({"recipient": target, "amount": amt})
        img = qrcode.make(data)
        filename = f"qr_pay_{target}_{amt:.2f}.png"
        filepath = os.path.join(os.path.expanduser("~"), "Desktop", filename)
        img.save(filepath)
        self.show_msg(f"QR code saved to Desktop: {filename}")

    def transfer_money(self):
        self.stdscr.clear()
        self.stdscr.addstr(2,2,"--- Transfer Funds ---")
        self.stdscr.addstr(4,2,"Recipient: "); self.stdscr.refresh()
        curses.echo(); target = self.stdscr.getstr(4,13,15).decode().strip().lower(); curses.noecho()
        self.stdscr.addstr(5,2,"Amount: $"); self.stdscr.refresh()
        curses.echo(); amt_str = self.stdscr.getstr(5,9,10).decode().strip(); curses.noecho()
        try:
            amt = float(amt_str)
            if amt <= 0:
                self.show_msg("Positive amount only."); return
        except:
            self.show_msg("Invalid amount."); return
        if self.net:
            resp = self.net.send({"cmd":"TRANSFER","recipient":target,"amount":amt})
            self.show_msg(resp.get("message","Transfer done"))
        else:
            self.show_msg("Transfer only in network mode.")
def show_chart(self):
        if not CHART: self.show_msg("Install matplotlib"); return
        if self.net:
            resp = self.net.history()
            if resp.get("status")!="ok": return
            data = resp["history"]
        else:
            data = self.user_data.get("transactions",[])
        if not data: self.show_msg("No transactions"); return
        amounts = [t["amount"] for t in data[-10:]]
        types = [1 if t["type"]=="DEPOSIT" else -1 for t in data[-10:]]
        plt.figure()
        plt.subplot(1,2,1); plt.pie([sum(1 for t in types if t==1), sum(1 for t in types if t==-1)], labels=["Deposits","Withdrawals"], autopct='%1.1f%%')
        plt.subplot(1,2,2); plt.bar(range(len(amounts)), amounts, color=['g' if x>0 else 'r' for x in types])
        plt.title("Last 10 transactions")
        plt.show(block=False)
        plt.pause(5)
        plt.close()

    def export_csv(self):
        if self.net:
            resp = self.net.history()
            if resp.get("status")!="ok": return
            data = resp["history"]
        else:
            data = self.user_data.get("transactions",[])
        if not data: self.show_msg("No transactions"); return
        path = os.path.expanduser("~/Desktop/wyllene_statement.csv")
        with open(path,'w',newline='') as f:
            w = csv.writer(f)
            w.writerow(["Time","Type","Amount"])
            for t in data:
                w.writerow([t["time"],t["type"],t["amount"]])
        self.show_msg(f"Exported to {path}")

    def play_sound(self, name):
        path = f"sounds/{name}.wav"
        if SOUND and os.path.exists(path):
            threading.Thread(target=playsound, args=(path,), daemon=True).start()
        else:
            print('\a',end='',flush=True)

    def input_dialog(self, prompt):
        self.stdscr.addstr(20,2,prompt); self.stdscr.refresh()
        curses.echo(); s = self.stdscr.getstr(20,len(prompt)+3,20).decode().strip(); curses.noecho()
        self.stdscr.move(20,2); self.stdscr.clrtoeol(); return s

    def show_msg(self, msg):
        self.stdscr.addstr(22,2,msg); self.stdscr.refresh(); self.stdscr.getch()

    def show_popup(self, title, items):
        # simple display
        self.stdscr.clear()
        self.stdscr.addstr(2,2,title)
        for i,item in enumerate(items[:15]):
            self.stdscr.addstr(4+i,2, f"{item['time']} {item['type']} ${item['amount']:.2f}")
        self.stdscr.addstr(22,2,"Press any key"); self.stdscr.getch()

    def save_local(self):
        with open("accounts.json","w") as f: json.dump(self.accounts, f)

def main():
    curses.wrapper(ATM)

if __name__ == "__main__":
    main()
