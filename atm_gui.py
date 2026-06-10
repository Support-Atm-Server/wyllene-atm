#!/usr/bin/env python3
import tkinter as tk
from tkinter import simpledialog
from tkinter import ttk, messagebox, scrolledtext
import json, socket, threading, simpledialog
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

HOST = "localhost"
PORT = 9999

class ATMClient:
    def __init__(self):
        self.sock = None
        self.username = None
        self.balance = 0.0

    def connect(self):
        self.sock = socket.socket()
        self.sock.connect((HOST, PORT))

    def send(self, cmd_dict):
        self.sock.sendall(json.dumps(cmd_dict).encode())
        return json.loads(self.sock.recv(4096).decode())

    def login(self, username, pin, security_answer):
        return self.send({"cmd":"LOGIN","username":username,"pin":pin,"security_answer":security_answer})

    def deposit(self, amount):
        return self.send({"cmd":"DEPOSIT","amount":amount})

    def withdraw(self, amount):
        return self.send({"cmd":"WITHDRAW","amount":amount})

    def transfer(self, recipient, amount):
        return self.send({"cmd":"TRANSFER","recipient":recipient,"amount":amount})

    def balance(self):
        return self.send({"cmd":"BALANCE"})

    def history(self):
        return self.send({"cmd":"HISTORY"})

class LoginWindow:
    def __init__(self, master, client, on_success):
        self.master = master
        self.client = client
        self.on_success = on_success
        self.master.title("Wyllene ATM - Login")
        self.master.geometry("350x250")
        self.master.resizable(False, False)

        ttk.Label(master, text="Username:").pack(pady=5)
        self.username_entry = ttk.Entry(master, width=25)
        self.username_entry.pack(pady=5)

        ttk.Label(master, text="PIN:").pack(pady=5)
        self.pin_entry = ttk.Entry(master, show="*", width=25)
        self.pin_entry.pack(pady=5)

        ttk.Label(master, text="Security Answer:").pack(pady=5)
        self.sec_entry = ttk.Entry(master, width=25)
        self.sec_entry.pack(pady=5)

        ttk.Button(master, text="Login", command=self.do_login).pack(pady=10)

    def do_login(self):
        username = self.username_entry.get().strip().lower()
        pin = self.pin_entry.get().strip()
        sec = self.sec_entry.get().strip()
        if not username or not pin or not sec:
            messagebox.showerror("Error", "All fields are required.")
            return
        try:
            resp = self.client.login(username, pin, sec)
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
            return
        if resp.get("status") == "ok":
            self.client.username = username
            self.client.balance = resp.get("balance", 0.0)
            self.master.destroy()
            self.on_success()
        else:
            messagebox.showerror("Login Failed", resp.get("message", "Invalid credentials"))

class MainDashboard:
    def __init__(self, master, client):
        self.master = master
        self.client = client
        self.master.title(f"Wyllene ATM - {client.username}")
        self.master.geometry("700x500")
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

        # Balance display
        self.balance_var = tk.StringVar(value=f"${client.balance:.2f}")
        ttk.Label(master, text="Current Balance", font=("Helvetica", 14)).pack(pady=10)
        ttk.Label(master, textvariable=self.balance_var, font=("Helvetica", 18, "bold")).pack(pady=5)

        # Transaction buttons
        btn_frame = ttk.Frame(master)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Deposit", command=self.deposit_window).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(btn_frame, text="Withdraw", command=self.withdraw_window).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(btn_frame, text="Transfer", command=self.transfer_window).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(btn_frame, text="Cardless", command=self.cardless_window).grid(row=0, column=3, padx=5, pady=5)
        ttk.Button(btn_frame, text="Bill Pay", command=self.billpay_window).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(btn_frame, text="Savings", command=self.savings_window).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(btn_frame, text="Invest", command=self.invest_window).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(btn_frame, text="Loans", command=self.loan_window).grid(row=1, column=3, padx=5, pady=5)
        ttk.Button(btn_frame, text="Convert", command=self.convert_window).grid(row=2, column=0, padx=5, pady=5)
        ttk.Button(btn_frame, text="AI Assistant", command=self.ai_assistant).grid(row=2, column=1, padx=5, pady=5)

        # History text area
        ttk.Label(master, text="Transaction History").pack(pady=(10,0))
        self.history_text = scrolledtext.ScrolledText(master, width=70, height=8, state='disabled')
        self.history_text.pack(pady=5)
        ttk.Button(master, text="Refresh History", command=self.load_history).pack(pady=5)

        # Chart button
        ttk.Button(master, text="Show Chart", command=self.show_chart).pack(pady=10)

        self.load_history()

    def load_history(self):
        try:
            resp = self.client.history()
        except:
            self.history_text.config(state='normal')
            self.history_text.insert(tk.END, "Could not load history.\n")
            self.history_text.config(state='disabled')
            return
        hist = resp.get("history", [])
        self.history_text.config(state='normal')
        self.history_text.delete(1.0, tk.END)
        for t in hist:
            self.history_text.insert(tk.END, f"{t['time']} {t['type']} ${t['amount']:.2f}\n")
        self.history_text.config(state='disabled')

    def deposit_window(self):
        win = tk.Toplevel(self.master)
        win.title("Deposit")
        win.geometry("250x120")
        ttk.Label(win, text="Amount:").pack(pady=5)
        entry = ttk.Entry(win, width=15)
        entry.pack(pady=5)
        def do():
            try:
                amt = float(entry.get())
                resp = self.client.deposit(amt)
                if resp.get("status") == "ok":
                    self.client.balance = resp["new_balance"]
                    self.balance_var.set(f"${self.client.balance:.2f}")
                    self.load_history()
                    win.destroy()
                else:
                    messagebox.showerror("Error", resp.get("message",""))
            except Exception as e:
                messagebox.showerror("Error", str(e))
        ttk.Button(win, text="Deposit", command=do).pack(pady=5)

    def withdraw_window(self):
        win = tk.Toplevel(self.master)
        win.title("Withdraw")
        win.geometry("250x120")
        ttk.Label(win, text="Amount:").pack(pady=5)
        entry = ttk.Entry(win, width=15)
        entry.pack(pady=5)
        def do():
            try:
                amt = float(entry.get())
                resp = self.client.withdraw(amt)
                if resp.get("status") == "ok":
                    self.client.balance = resp["new_balance"]
                    self.balance_var.set(f"${self.client.balance:.2f}")
                    self.load_history()
                    win.destroy()
                else:
                    messagebox.showerror("Error", resp.get("message",""))
            except Exception as e:
                messagebox.showerror("Error", str(e))
        ttk.Button(win, text="Withdraw", command=do).pack(pady=5)

    def transfer_window(self):
        win = tk.Toplevel(self.master)
        win.title("Transfer")
        win.geometry("250x170")
        ttk.Label(win, text="Recipient:").pack(pady=5)
        recp_entry = ttk.Entry(win, width=15)
        recp_entry.pack(pady=5)
        ttk.Label(win, text="Amount:").pack(pady=5)
        amt_entry = ttk.Entry(win, width=15)
        amt_entry.pack(pady=5)
        def do():
            try:
                target = recp_entry.get().strip().lower()
                amt = float(amt_entry.get())
                resp = self.client.transfer(target, amt)
                if resp.get("status") == "ok":
                    # Update balance
                    resp_bal = self.client.balance()
                    if resp_bal.get("status") == "ok":
                        self.client.balance = resp_bal["balance"]
                        self.balance_var.set(f"${self.client.balance:.2f}")
                    self.load_history()
                    win.destroy()
                else:
                    messagebox.showerror("Error", resp.get("message",""))
            except Exception as e:
                messagebox.showerror("Error", str(e))
        ttk.Button(win, text="Transfer", command=do).pack(pady=5)

    def show_chart(self):
        resp = self.client.history()
        hist = resp.get("history", [])
        if not hist:
            messagebox.showinfo("No Data", "No transactions to chart.")
            return
        amounts = [t["amount"] for t in hist[-10:]]
        types = [1 if t["type"] == "DEPOSIT" else -1 for t in hist[-10:]]
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4))
        ax1.pie([sum(1 for t in types if t==1), sum(1 for t in types if t==-1)],
                labels=["Deposits","Withdrawals"], autopct='%1.1f%%')
        ax2.bar(range(len(amounts)), amounts, color=['g' if x>0 else 'r' for x in types])
        ax2.set_title("Last 10 transactions")
        chart_win = tk.Toplevel(self.master)
        chart_win.title("Transaction Chart")
        canvas = FigureCanvasTkAgg(fig, master=chart_win)
        canvas.draw()
        canvas.get_tk_widget().pack()
        # Do not block; let user close chart window


    def ai_assistant(self):
        msg = simpledialog.askstring("AI Assistant", "How can I help you?")
        if not msg:
            return
        try:
            resp = self.client.send({"cmd":"AI_ASSIST","message":msg})
            if resp.get("status") == "ok":
                messagebox.showinfo("AI Reply", resp.get("reply",""))
            else:
                messagebox.showerror("Error", "AI service unavailable.")
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def cardless_window(self):
        win = tk.Toplevel(self.master)
        win.title("Cardless Withdrawal Code")
        win.geometry("250x120")
        ttk.Label(win, text="Amount:").pack(pady=5)
        entry = ttk.Entry(win, width=15)
        entry.pack(pady=5)
        def do():
            try:
                amt = float(entry.get())
                resp = self.client.send({"cmd":"CARDLESS_GENERATE","amount":amt})
                if resp.get("status") == "ok":
                    messagebox.showinfo("Cardless Code", f"Code: {resp['code']}\nAmount: ${resp['amount']:.2f}\nExpires: {resp['expires']}")
                else:
                    messagebox.showerror("Error", resp.get("message",""))
            except Exception as e:
                messagebox.showerror("Error", str(e))
            win.destroy()
        ttk.Button(win, text="Generate", command=do).pack(pady=5)

    def billpay_window(self):
        win = tk.Toplevel(self.master)
        win.title("Pay a Bill")
        win.geometry("250x170")
        ttk.Label(win, text="Biller:").pack(pady=5)
        biller_entry = ttk.Entry(win, width=15)
        biller_entry.pack(pady=5)
        ttk.Label(win, text="Amount:").pack(pady=5)
        amt_entry = ttk.Entry(win, width=15)
        amt_entry.pack(pady=5)
        def do():
            try:
                biller = biller_entry.get().strip()
                amt = float(amt_entry.get())
                resp = self.client.send({"cmd":"BILL_PAY","biller":biller,"amount":amt})
                if resp.get("status") == "ok":
                    self.client.balance = resp["new_balance"]
                    self.balance_var.set(f"${self.client.balance:.2f}")
                    self.load_history()
                    win.destroy()
                else:
                    messagebox.showerror("Error", resp.get("message",""))
            except Exception as e:
                messagebox.showerror("Error", str(e))
        ttk.Button(win, text="Pay", command=do).pack(pady=5)

    def savings_window(self):
        win = tk.Toplevel(self.master)
        win.title("Savings Goals")
        win.geometry("300x200")
        ttk.Label(win, text="Goal Name:").pack(pady=5)
        name_entry = ttk.Entry(win, width=20)
        name_entry.pack(pady=5)
        ttk.Label(win, text="Target Amount:").pack(pady=5)
        target_entry = ttk.Entry(win, width=20)
        target_entry.pack(pady=5)
        def create_goal():
            name = name_entry.get().strip()
            try:
                target = float(target_entry.get())
                resp = self.client.send({"cmd":"SAVINGS_GOAL_CREATE","goal_name":name,"target":target})
                if resp.get("status") == "ok":
                    messagebox.showinfo("Success", f"Goal '{name}' created.")
                else:
                    messagebox.showerror("Error", resp.get("message",""))
            except:
                messagebox.showerror("Error", "Invalid input.")
        ttk.Button(win, text="Create Goal", command=create_goal).pack(pady=5)
        # Contribution part (simplified: ask for goal name and amount)
        ttk.Label(win, text="Contribute to Goal:").pack(pady=(10,0))
        goal_name_cont = ttk.Entry(win, width=20)
        goal_name_cont.pack(pady=5)
        amt_cont = ttk.Entry(win, width=20)
        amt_cont.pack(pady=5)
        def contribute():
            gname = goal_name_cont.get().strip()
            try:
                amt = float(amt_cont.get())
                resp = self.client.send({"cmd":"SAVINGS_GOAL_CONTRIBUTE","goal_name":gname,"amount":amt})
                if resp.get("status") == "ok":
                    self.client.balance = resp["new_balance"]
                    self.balance_var.set(f"${self.client.balance:.2f}")
                    self.load_history()
                    messagebox.showinfo("Success", f"Added ${amt:.2f} to '{gname}'")
                else:
                    messagebox.showerror("Error", resp.get("message",""))
            except:
                messagebox.showerror("Error", "Invalid amount.")
        ttk.Button(win, text="Contribute", command=contribute).pack(pady=5)


    def invest_window(self):
        win = tk.Toplevel(self.master)
        win.title("Investments")
        win.geometry("300x250")
        ttk.Label(win, text="Symbol:").pack(pady=5)
        sym_entry = ttk.Entry(win, width=10)
        sym_entry.pack(pady=5)
        ttk.Label(win, text="Amount ($):").pack(pady=5)
        amt_entry = ttk.Entry(win, width=10)
        amt_entry.pack(pady=5)
        def buy():
            sym = sym_entry.get().upper().strip()
            try:
                amt = float(amt_entry.get())
                resp = self.client.send({"cmd":"INVEST_BUY","symbol":sym,"amount":amt})
                messagebox.showinfo("Result", resp.get("message",""))
                self.update_balance()
            except:
                messagebox.showerror("Error","Invalid input")
        ttk.Button(win, text="Buy", command=buy).pack(pady=5)
        ttk.Label(win, text="Sell Quantity:").pack(pady=5)
        qty_entry = ttk.Entry(win, width=10)
        qty_entry.pack(pady=5)
        def sell():
            sym = sym_entry.get().upper().strip()
            try:
                qty = float(qty_entry.get())
                resp = self.client.send({"cmd":"INVEST_SELL","symbol":sym,"quantity":qty})
                messagebox.showinfo("Result", resp.get("message",""))
                self.update_balance()
            except:
                messagebox.showerror("Error","Invalid input")
        ttk.Button(win, text="Sell", command=sell).pack(pady=5)
        def view_portfolio():
            resp = self.client.send({"cmd":"INVEST_PORTFOLIO"})
            if resp.get("status")=="ok":
                port = resp.get("portfolio",[])
                if port:
                    lines = [f"{p['symbol']}: {p['quantity']:.2f} sh @ ${p['current_price']:.2f} = ${p['value']:.2f}" for p in port]
                    messagebox.showinfo("Portfolio", "\n".join(lines) + f"\nTotal: ${resp['total_value']:.2f}")
                else:
                    messagebox.showinfo("Portfolio", "No holdings.")
            else:
                messagebox.showerror("Error","Could not fetch portfolio")
        ttk.Button(win, text="View Portfolio", command=view_portfolio).pack(pady=5)

    def loan_window(self):
        win = tk.Toplevel(self.master)
        win.title("Loans")
        win.geometry("300x250")
        ttk.Label(win, text="Loan Amount ($):").pack(pady=5)
        principal_entry = ttk.Entry(win, width=15)
        principal_entry.pack(pady=5)
        ttk.Label(win, text="Term (months):").pack(pady=5)
        term_entry = ttk.Entry(win, width=10)
        term_entry.pack(pady=5)
        def request():
            try:
                p = float(principal_entry.get())
                t = int(term_entry.get())
                resp = self.client.send({"cmd":"LOAN_REQUEST","principal":p,"term":t})
                messagebox.showinfo("Result", resp.get("message",""))
                self.update_balance()
            except:
                messagebox.showerror("Error","Invalid input")
        ttk.Button(win, text="Request Loan", command=request).pack(pady=5)
        ttk.Label(win, text="Loan ID:").pack(pady=5)
        loan_id_entry = ttk.Entry(win, width=10)
        loan_id_entry.pack(pady=5)
        ttk.Label(win, text="Payment ($):").pack(pady=5)
        pay_amt_entry = ttk.Entry(win, width=10)
        pay_amt_entry.pack(pady=5)
        def pay():
            try:
                lid = int(loan_id_entry.get())
                amt = float(pay_amt_entry.get())
                resp = self.client.send({"cmd":"LOAN_PAY","loan_id":lid,"amount":amt})
                messagebox.showinfo("Result", resp.get("message",""))
                self.update_balance()
            except:
                messagebox.showerror("Error","Invalid input")
        ttk.Button(win, text="Make Payment", command=pay).pack(pady=5)
        def status():
            resp = self.client.send({"cmd":"LOAN_STATUS"})
            if resp.get("status")=="ok":
                loans = resp.get("loans",[])
                if loans:
                    lines = [f"ID:{l['loan_id']} Rem:{l['remaining']:.2f} Month:{l['monthly_payment']:.2f}" for l in loans]
                    messagebox.showinfo("Loans", "\n".join(lines))
                else:
                    messagebox.showinfo("Loans", "No active loans.")
            else:
                messagebox.showerror("Error","Could not fetch loans")
        ttk.Button(win, text="Loan Status", command=status).pack(pady=5)

    def convert_window(self):
        win = tk.Toplevel(self.master)
        win.title("Currency Converter")
        win.geometry("250x200")
        ttk.Label(win, text="From:").pack(pady=5)
        from_entry = ttk.Entry(win, width=10)
        from_entry.pack(pady=5)
        ttk.Label(win, text="To:").pack(pady=5)
        to_entry = ttk.Entry(win, width=10)
        to_entry.pack(pady=5)
        ttk.Label(win, text="Amount:").pack(pady=5)
        amt_entry = ttk.Entry(win, width=10)
        amt_entry.pack(pady=5)
        def convert():
            f = from_entry.get().upper().strip()
            t = to_entry.get().upper().strip()
            try:
                a = float(amt_entry.get())
                resp = self.client.send({"cmd":"CURRENCY_CONVERT","from":f,"to":t,"amount":a})
                if resp.get("status")=="ok":
                    messagebox.showinfo("Result", f"{a} {f} = {resp['converted']} {t}")
                else:
                    messagebox.showerror("Error", resp.get("message",""))
            except:
                messagebox.showerror("Error","Invalid amount")
        ttk.Button(win, text="Convert", command=convert).pack(pady=10)

    def update_balance(self):
        try:
            resp = self.client.balance()
            if resp.get("status") == "ok":
                self.client.balance = resp["balance"]
                self.balance_var.set(f"${self.client.balance:.2f}")
        except:
            pass

    def on_close(self):
        self.master.destroy()

def main():
    client = ATMClient()
    try:
        client.connect()
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Connection Error", f"Cannot connect to server: {e}")
        return

    root = tk.Tk()
    def launch_dashboard():
        dash_root = tk.Toplevel()
        MainDashboard(dash_root, client)
        dash_root.protocol("WM_DELETE_WINDOW", lambda: (dash_root.destroy(), root.quit()))
        root.withdraw()  # hide login window
    LoginWindow(root, client, launch_dashboard)
    root.mainloop()
    client.sock.close()

if __name__ == "__main__":
    main()
