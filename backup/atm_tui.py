#!/usr/bin/env python3

import json
import os
import sys
import curses
from datetime import datetime
import threading
import subprocess
import csv
import base64

# Attempt imports for optional features
try:
    from playsound import playsound
    SOUND_ENABLED = True
except ImportError:
    SOUND_ENABLED = False
    def playsound(file, block=False):
        print('\a', end='', flush=True)

try:
    from cryptography.fernet import Fernet
    ENCRYPTION_ENABLED = True
except ImportError:
    ENCRYPTION_ENABLED = False

# ---------- Encryption Setup ----------
ACCOUNTS_FILE = "accounts.json"
ENCRYPTED_FILE = "accounts.enc"
# Hardcoded key (you can change this; in production you'd use a key file or env var)
# For simplicity, we'll use a fixed key derived from a password.
# In this version we'll keep the key inside the script – not perfect but works for a project.
ENCRYPTION_KEY = b'Y7qDBDOr-1lSSHY12tnq46oLQv23vg08GvV8V8Fr4MY='  # Will be replaced by sed below

# We'll use a simple password-based encryption: if encrypted file exists, load it; else fallback to JSON.

def get_cipher():
    if not ENCRYPTION_ENABLED:
        return None
    return Fernet(ENCRYPTION_KEY)

def load_accounts():
    cipher = get_cipher()
    if cipher and os.path.exists(ENCRYPTED_FILE):
        with open(ENCRYPTED_FILE, 'rb') as f:
            encrypted_data = f.read()
        decrypted = cipher.decrypt(encrypted_data)
        return json.loads(decrypted.decode())
    elif os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, 'r') as f:
            data = json.load(f)
        # Migrate to encrypted
        save_accounts(data)
        return data
    else:
        # Brand new default account
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
    cipher = get_cipher()
    if cipher:
        json_data = json.dumps(accounts, indent=4).encode()
        encrypted = cipher.encrypt(json_data)
        with open(ENCRYPTED_FILE, 'wb') as f:
            f.write(encrypted)
        # Remove plain JSON if exists
        if os.path.exists(ACCOUNTS_FILE):
            os.remove(ACCOUNTS_FILE)
    else:
        with open(ACCOUNTS_FILE, 'w') as f:
            json.dump(accounts, f, indent=4)

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
    save_accounts(accounts)

def speak(text):
    """Use espeak to speak text asynchronously."""
    try:
        subprocess.Popen(['espeak', text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass  # fail silently

def export_to_csv(user_data, username):
    """Export transactions to CSV file on Desktop."""
    transactions = user_data.get("transactions", [])
    if not transactions:
        return False
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    filename = f"wyllene_{username}_statement.csv"
    filepath = os.path.join(desktop, filename)
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Time", "Type", "Amount", "Running Balance"])
        running = 0.0
        for t in transactions:
            if t["type"] == "DEPOSIT":
                running += t["amount"]
            else:
                running -= t["amount"]
            writer.writerow([t["time"], t["type"], f"${t['amount']:.2f}", f"${running:.2f}"])
    return filepath

# ---------- Curses TUI Class ----------
class WylleneATM:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.accounts = load_accounts()
        self.username = None
        self.user_data = None
        self.current_row = 0
        self.menu_options = [
            "Check Balance",
            "Deposit Money",
            "Withdraw Money",
            "Transaction History",
            "Change PIN",
            "Spending Chart",
            "Export to CSV",
            "Exit"
        ]
        self.admin_menu_options = [
            "View All Accounts",
            "Reset User PIN",
            "Return to Main Menu"
        ]
        self.status_message = ""
        self.status_colour = 1
        self.init_colours()
        self.run()

    def init_colours(self):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLUE)

    def draw_header(self):
        h, w = self.stdscr.getmaxyx()
        title = " 🏦  WYLLENE ATM SYSTEM  🏦 "
        self.stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
        self.stdscr.addstr(0, (w - len(title)) // 2, title)
        self.stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
        self.stdscr.hline(1, 0, curses.ACS_HLINE, w)

    def draw_info_panel(self):
        h, w = self.stdscr.getmaxyx()
        if self.username and self.username != "admin":
            welcome = f" 👤 Welcome, {self.username}!"
            balance = f" 💰 Balance: ${self.user_data['balance']:.2f}"
            self.stdscr.addstr(3, 2, welcome)
            self.stdscr.addstr(4, 2, balance, curses.color_pair(2) | curses.A_BOLD)
        elif self.username == "admin":
            self.stdscr.addstr(3, 2, "🔐 ADMIN MODE", curses.color_pair(1) | curses.A_BOLD)
        else:
            self.stdscr.addstr(3, 2, "Please log in first.")

    def draw_menu(self):
        h, w = self.stdscr.getmaxyx()
        menu_start_y = 7
        self.stdscr.addstr(menu_start_y, 2, "Select an option:")
        options = self.menu_options if self.username != "admin" else self.admin_menu_options
        for idx, option in enumerate(options):
            x = 4
            y = menu_start_y + 2 + idx
            if idx == self.current_row:
                self.stdscr.attron(curses.color_pair(5))
                self.stdscr.addstr(y, x, f"▸ {idx+1}. {option}")
                self.stdscr.attroff(curses.color_pair(5))
            else:
                self.stdscr.addstr(y, x, f"  {idx+1}. {option}")
        hint_y = menu_start_y + 2 + len(options) + 1
        self.stdscr.addstr(hint_y, 2, "↑/↓: Navigate   Enter: Select   Q: Quit")

    def draw_status_bar(self):
        h, w = self.stdscr.getmaxyx()
        status_y = h - 2
        self.stdscr.hline(status_y, 0, curses.ACS_HLINE, w)
        if self.status_message:
            colour = curses.color_pair(self.status_colour)
            self.stdscr.addstr(status_y + 1, 2, self.status_message[:w-4], colour)
        else:
            self.stdscr.addstr(status_y + 1, 2, "Ready.")

    def refresh_ui(self):
        self.stdscr.clear()
        self.draw_header()
        self.draw_info_panel()
        self.draw_menu()
        self.draw_status_bar()
        self.stdscr.refresh()

    def set_status(self, msg, is_error=False, is_success=False):
        self.status_message = msg
        if is_error:
            self.status_colour = 3
            self.play_sound("error")
            speak("Error. " + msg)
        elif is_success:
            self.status_colour = 2
            self.play_sound("login")
            speak("Success. " + msg)
        else:
            self.status_colour = 1

    def play_sound(self, sound_name):
        if not SOUND_ENABLED:
            return
        sound_path = os.path.join(os.path.dirname(__file__), "sounds", f"{sound_name}.wav")
        if os.path.exists(sound_path):
            threading.Thread(target=playsound, args=(sound_path,), daemon=True).start()
        else:
            print('\a', end='', flush=True)

    def input_dialog(self, prompt):
        h, w = self.stdscr.getmaxyx()
        input_y = h - 4
        self.stdscr.addstr(input_y, 2, prompt)
        self.stdscr.refresh()
        curses.echo()
        user_input = self.stdscr.getstr(input_y, len(prompt)+3, 60).decode('utf-8')
        curses.noecho()
        self.stdscr.move(input_y, 2)
        self.stdscr.clrtoeol()
        return user_input

    def login_screen(self):
        h, w = self.stdscr.getmaxyx()
        self.stdscr.clear()
        self.draw_header()
        self.stdscr.addstr(4, 2, "🔐 LOGIN")
        self.stdscr.addstr(6, 2, "Username: ")
        self.stdscr.refresh()
        curses.echo()
        username = self.stdscr.getstr(6, 12, 20).decode('utf-8').strip().lower()
        self.stdscr.addstr(8, 2, "PIN: ")
        pin = self.stdscr.getstr(8, 7, 20).decode('utf-8').strip()
        curses.noecho()

        if username == "admin" and pin == "admin123":
            self.play_sound("login")
            speak("Admin logged in")
            self.username = "admin"
            self.user_data = None
            return "admin"
        elif username in self.accounts and self.accounts[username]["pin"] == pin:
            self.play_sound("login")
            speak(f"Welcome {username}")
            self.username = username
            self.user_data = self.accounts[username]
            return True
        else:
            self.play_sound("error")
            speak("Invalid login")
            self.set_status("Invalid username or PIN.", is_error=True)
            self.stdscr.getch()
            return False

    def run(self):
        while not self.username:
            result = self.login_screen()
            if result == "admin":
                self.admin_panel()
                self.username = None
            elif not result:
                continue

        while True:
            self.refresh_ui()
            key = self.stdscr.getch()

            if key == curses.KEY_UP:
                self.current_row = (self.current_row - 1) % len(self.menu_options)
            elif key == curses.KEY_DOWN:
                self.current_row = (self.current_row + 1) % len(self.menu_options)
            elif key in [curses.KEY_ENTER, 10, 13]:
                self.handle_selection()
            elif key == ord('q'):
                break

            if self.user_data and self.user_data.get("transactions"):
                last = self.user_data["transactions"][-1]
                self.set_status(f"Last: {last['type']} ${last['amount']:.2f} on {last['time']}")

    def handle_selection(self):
        choice = self.menu_options[self.current_row]
        if choice == "Check Balance":
            self.set_status(f"Balance: ${self.user_data['balance']:.2f}", is_success=True)
        elif choice == "Deposit Money":
            amount_str = self.input_dialog("Enter amount to deposit: $")
            try:
                amount = float(amount_str)
                if amount <= 0:
                    self.set_status("Amount must be positive.", is_error=True)
                else:
                    self.user_data["balance"] += amount
                    record_transaction(self.accounts, self.username, "DEPOSIT", amount)
                    self.play_sound("deposit")
                    speak(f"Deposited {amount} dollars")
                    self.set_status(f"Deposited ${amount:.2f}", is_success=True)
            except ValueError:
                self.set_status("Invalid number.", is_error=True)
        elif choice == "Withdraw Money":
            amount_str = self.input_dialog("Enter amount to withdraw: $")
            try:
                amount = float(amount_str)
                if amount <= 0:
                    self.set_status("Amount must be positive.", is_error=True)
                elif amount > self.user_data["balance"]:
                    self.set_status("Insufficient funds.", is_error=True)
                else:
                    self.user_data["balance"] -= amount
                    record_transaction(self.accounts, self.username, "WITHDRAW", amount)
                    self.play_sound("withdraw")
                    speak(f"Withdrew {amount} dollars")
                    self.set_status(f"Withdrew ${amount:.2f}", is_success=True)
            except ValueError:
                self.set_status("Invalid number.", is_error=True)
        elif choice == "Transaction History":
            self.show_history()
        elif choice == "Change PIN":
            self.change_pin()
        elif choice == "Spending Chart":
            self.show_chart()
        elif choice == "Export to CSV":
            self.export_csv()
        elif choice == "Exit":
            sys.exit(0)

    def show_history(self):
        transactions = self.user_data.get("transactions", [])
        if not transactions:
            self.set_status("No transactions yet.", is_error=False)
            return
        running_balance = 0.0
        history_lines = []
        for t in transactions:
            if t["type"] == "DEPOSIT":
                running_balance += t["amount"]
                colour_pair = curses.color_pair(2)
            else:
                running_balance -= t["amount"]
                colour_pair = curses.color_pair(3)
            line = f"{t['time']}  {t['type']:8}  ${t['amount']:8.2f}  Balance: ${running_balance:.2f}"
            history_lines.append((line, colour_pair))
        h, w = self.stdscr.getmaxyx()
        popup_h = min(20, h - 4)
        popup_w = min(80, w - 4)
        start_y = (h - popup_h) // 2
        start_x = (w - popup_w) // 2
        pad = curses.newpad(len(history_lines) + 2, popup_w - 2)
        pad.keypad(True)
        pad.addstr(0, 0, " TRANSACTION HISTORY ", curses.color_pair(1) | curses.A_BOLD)
        for i, (line, colour) in enumerate(history_lines):
            try:
                pad.addstr(i + 2, 1, line[:popup_w-3], colour)
            except curses.error:
                pass
        top_line = 0
        while True:
            self.stdscr.attron(curses.color_pair(1))
            for y in range(start_y, start_y + popup_h):
                self.stdscr.addch(y, start_x, curses.ACS_VLINE)
                self.stdscr.addch(y, start_x + popup_w - 1, curses.ACS_VLINE)
            self.stdscr.hline(start_y, start_x, curses.ACS_HLINE, popup_w)
            self.stdscr.hline(start_y + popup_h - 1, start_x, curses.ACS_HLINE, popup_w)
            self.stdscr.addch(start_y, start_x, curses.ACS_ULCORNER)
            self.stdscr.addch(start_y, start_x + popup_w - 1, curses.ACS_URCORNER)
            self.stdscr.addch(start_y + popup_h - 1, start_x, curses.ACS_LLCORNER)
            self.stdscr.addch(start_y + popup_h - 1, start_x + popup_w - 1, curses.ACS_LRCORNER)
            self.stdscr.attroff(curses.color_pair(1))
            title = " TRANSACTION HISTORY "
            self.stdscr.addstr(start_y, start_x + (popup_w - len(title)) // 2, title, curses.color_pair(1) | curses.A_BOLD)
            pad.refresh(top_line, 0, start_y + 1, start_x + 1, start_y + popup_h - 2, start_x + popup_w - 2)
            instr = " ↑/↓: Scroll   Q: Close "
            self.stdscr.addstr(start_y + popup_h - 2, start_x + (popup_w - len(instr)) // 2, instr, curses.A_REVERSE)
            self.stdscr.refresh()
            key = pad.getch()
            if key == curses.KEY_UP and top_line > 0:
                top_line -= 1
            elif key == curses.KEY_DOWN and top_line < len(history_lines) - (popup_h - 4):
                top_line += 1
            elif key == ord('q') or key == ord('Q') or key == 27:
                break
        self.refresh_ui()

    def change_pin(self):
        old = self.input_dialog("Current PIN: ")
        if old != self.user_data["pin"]:
            self.set_status("Incorrect PIN.", is_error=True)
            return
        new = self.input_dialog("New PIN (4 digits): ")
        if not new.isdigit() or len(new) != 4:
            self.set_status("PIN must be 4 digits.", is_error=True)
            return
        confirm = self.input_dialog("Confirm new PIN: ")
        if new != confirm:
            self.set_status("PINs do not match.", is_error=True)
            return
        self.user_data["pin"] = new
        save_accounts(self.accounts)
        self.play_sound("login")
        speak("PIN changed")
        self.set_status("PIN changed successfully!", is_success=True)

    def show_chart(self):
        transactions = self.user_data.get("transactions", [])
        if not transactions:
            self.set_status("No transactions yet.", is_error=False)
            return
        recent = transactions[-5:]
        labels = []
        amounts = []
        types = []
        for t in recent:
            short_time = t["time"][5:16]
            labels.append(short_time)
            amounts.append(t["amount"])
            types.append(t["type"])
        max_amount = max(amounts) if amounts else 1
        bar_width = 20
        h, w = self.stdscr.getmaxyx()
        popup_h = min(10 + len(recent), h - 4)
        popup_w = min(60, w - 4)
        start_y = (h - popup_h) // 2
        start_x = (w - popup_w) // 2
        lines = ["   SPENDING CHART (last 5 transactions)   "]
        lines.append("-" * (popup_w - 4))
        for i, (label, amt, ttype) in enumerate(zip(labels, amounts, types)):
            bar_len = int((amt / max_amount) * bar_width) if max_amount > 0 else 0
            bar_char = "█" if ttype == "DEPOSIT" else "░"
            bar = bar_char * bar_len
            colour = curses.color_pair(2) if ttype == "DEPOSIT" else curses.color_pair(3)
            line = f"{label}  {ttype[0]} ${amt:7.2f}  {bar}"
            lines.append((line, colour))
        lines.append("-" * (popup_w - 4))
        lines.append(" Press any key to close ")
        pad = curses.newpad(len(lines), popup_w - 2)
        for i, item in enumerate(lines):
            if isinstance(item, tuple):
                line, colour = item
                pad.addstr(i, 1, line[:popup_w-3], colour)
            else:
                if i == 0:
                    pad.addstr(i, 1, item, curses.color_pair(1) | curses.A_BOLD)
                else:
                    pad.addstr(i, 1, item)
        self.stdscr.attron(curses.color_pair(1))
        for y in range(start_y, start_y + popup_h):
            self.stdscr.addch(y, start_x, curses.ACS_VLINE)
            self.stdscr.addch(y, start_x + popup_w - 1, curses.ACS_VLINE)
        self.stdscr.hline(start_y, start_x, curses.ACS_HLINE, popup_w)
        self.stdscr.hline(start_y + popup_h - 1, start_x, curses.ACS_HLINE, popup_w)
        self.stdscr.addch(start_y, start_x, curses.ACS_ULCORNER)
        self.stdscr.addch(start_y, start_x + popup_w - 1, curses.ACS_URCORNER)
        self.stdscr.addch(start_y + popup_h - 1, start_x, curses.ACS_LLCORNER)
        self.stdscr.addch(start_y + popup_h - 1, start_x + popup_w - 1, curses.ACS_LRCORNER)
        self.stdscr.attroff(curses.color_pair(1))
        pad.refresh(0, 0, start_y + 1, start_x + 1, start_y + popup_h - 2, start_x + popup_w - 2)
        self.stdscr.refresh()
        self.stdscr.getch()
        self.refresh_ui()

    def export_csv(self):
        filepath = export_to_csv(self.user_data, self.username)
        if filepath:
            self.set_status(f"Exported to {filepath}", is_success=True)
            speak("Statement exported to CSV")
        else:
            self.set_status("No transactions to export.", is_error=True)

    # ---------- Admin Functions ----------
    def admin_panel(self):
        current_row = 0
        while True:
            self.stdscr.clear()
            self.draw_header()
            self.stdscr.addstr(3, 2, "🔐 ADMIN MODE", curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(5, 2, f"Total Accounts: {len(self.accounts)}")
            total_assets = sum(acc["balance"] for acc in self.accounts.values())
            self.stdscr.addstr(6, 2, f"Total Bank Assets: ${total_assets:.2f}", curses.color_pair(2))
            menu_start = 9
            self.stdscr.addstr(menu_start, 2, "Admin Options:")
            for idx, opt in enumerate(self.admin_menu_options):
                y = menu_start + 2 + idx
                if idx == current_row:
                    self.stdscr.attron(curses.color_pair(5))
                    self.stdscr.addstr(y, 4, f"▸ {opt}")
                    self.stdscr.attroff(curses.color_pair(5))
                else:
                    self.stdscr.addstr(y, 4, f"  {opt}")
            self.stdscr.addstr(menu_start + 2 + len(self.admin_menu_options) + 2, 2,
                               "↑/↓: Navigate   Enter: Select   Q: Exit Admin")
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if key == curses.KEY_UP:
                current_row = (current_row - 1) % len(self.admin_menu_options)
            elif key == curses.KEY_DOWN:
                current_row = (current_row + 1) % len(self.admin_menu_options)
            elif key in [curses.KEY_ENTER, 10, 13]:
                choice = self.admin_menu_options[current_row]
                if choice == "View All Accounts":
                    self.view_all_accounts()
                elif choice == "Reset User PIN":
                    self.reset_user_pin()
                elif choice == "Return to Main Menu":
                    break
            elif key == ord('q'):
                break

    def view_all_accounts(self):
        h, w = self.stdscr.getmaxyx()
        lines = ["USERNAME         BALANCE"]
        lines.append("-" * 30)
        for uname, data in self.accounts.items():
            lines.append(f"{uname:<16} ${data['balance']:>10.2f}")
        lines.append("-" * 30)
        lines.append(f"{'TOTAL':<16} ${sum(a['balance'] for a in self.accounts.values()):>10.2f}")
        popup_h = min(len(lines)+4, h-4)
        popup_w = min(40, w-4)
        start_y = (h - popup_h) // 2
        start_x = (w - popup_w) // 2
        pad = curses.newpad(len(lines), popup_w-2)
        for i, line in enumerate(lines):
            pad.addstr(i, 0, line[:popup_w-3])
        top_line = 0
        while True:
            self.stdscr.attron(curses.color_pair(1))
            for y in range(start_y, start_y+popup_h):
                self.stdscr.addch(y, start_x, curses.ACS_VLINE)
                self.stdscr.addch(y, start_x+popup_w-1, curses.ACS_VLINE)
            self.stdscr.hline(start_y, start_x, curses.ACS_HLINE, popup_w)
            self.stdscr.hline(start_y+popup_h-1, start_x, curses.ACS_HLINE, popup_w)
            self.stdscr.addch(start_y, start_x, curses.ACS_ULCORNER)
            self.stdscr.addch(start_y, start_x+popup_w-1, curses.ACS_URCORNER)
            self.stdscr.addch(start_y+popup_h-1, start_x, curses.ACS_LLCORNER)
            self.stdscr.addch(start_y+popup_h-1, start_x+popup_w-1, curses.ACS_LRCORNER)
            self.stdscr.attroff(curses.color_pair(1))
            self.stdscr.addstr(start_y, start_x+2, " ALL ACCOUNTS ", curses.color_pair(1))
            pad.refresh(top_line, 0, start_y+1, start_x+1, start_y+popup_h-2, start_x+popup_w-2)
            self.stdscr.addstr(start_y+popup_h-2, start_x+2, "↑/↓ Scroll  Q Close")
            self.stdscr.refresh()
            key = pad.getch()
            if key == curses.KEY_UP and top_line > 0:
                top_line -= 1
            elif key == curses.KEY_DOWN and top_line < len(lines) - (popup_h-3):
                top_line += 1
            elif key == ord('q'):
                break

    def reset_user_pin(self):
        username = self.input_dialog("Enter username to reset PIN: ").strip().lower()
        if username not in self.accounts:
            self.set_status(f"User '{username}' not found.", is_error=True)
            self.stdscr.getch()
            return
        new_pin = self.input_dialog("Enter new 4-digit PIN: ")
        if not new_pin.isdigit() or len(new_pin) != 4:
            self.set_status("PIN must be exactly 4 digits.", is_error=True)
            self.stdscr.getch()
            return
        self.accounts[username]["pin"] = new_pin
        save_accounts(self.accounts)
        self.play_sound("login")
        speak(f"PIN reset for {username}")
        self.set_status(f"PIN for '{username}' reset successfully!", is_success=True)
        self.stdscr.getch()

def main():
    curses.wrapper(WylleneATM)

if __name__ == "__main__":
    main()
