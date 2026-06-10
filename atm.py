#!/usr/bin/env python3

import json
import os
import sys
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

ACCOUNTS_FILE = "accounts.json"
DEFAULT_USERNAME = "wyllene"
DEFAULT_PIN = "1234"
INITIAL_BALANCE = 1000.0

def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        accounts = {
            DEFAULT_USERNAME: {
                "pin": DEFAULT_PIN,
                "balance": INITIAL_BALANCE,
                "transactions": []
            }
        }
        save_accounts(accounts)
        return accounts
    else:
        with open(ACCOUNTS_FILE, "r") as f:
            data = json.load(f)
        if "pin" in data:
            accounts = {
                DEFAULT_USERNAME: {
                    "pin": data["pin"],
                    "balance": data["balance"],
                    "transactions": data.get("transactions", [])
                }
            }
            save_accounts(accounts)
            return accounts
        else:
            return data

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts, f, indent=4)

def clear_screen():
    os.system("clear")

def print_header():
    print(Fore.CYAN + "=" * 44)
    print(Fore.YELLOW + "         🏦  WYLLENE ATM SYSTEM  🏦")
    print(Fore.CYAN + "=" * 44 + Style.RESET_ALL)

def authenticate(accounts):
    print(Fore.CYAN + "\nPlease log in.")
    username = input("Username: ").strip().lower()
    if username not in accounts:
        print(Fore.RED + f"No account found for {username}.")
        return None, None
    user_data = accounts[username]
    attempts = 3
    while attempts > 0:
        pin = input("PIN: ")
        if pin == user_data["pin"]:
            return username, user_data
        else:
            attempts -= 1
            print(Fore.RED + f"Incorrect PIN. {attempts} attempt(s) remaining.")
    print(Fore.RED + "Too many failed attempts. Exiting.")
    return None, None

def show_menu(username):
    print(f"\n{Fore.GREEN}Welcome, {username}!")
    print(Fore.CYAN + "1. Check Balance")
    print(Fore.CYAN + "2. Deposit Money")
    print(Fore.CYAN + "3. Withdraw Money")
    print(Fore.CYAN + "4. Transaction History")
    print(Fore.CYAN + "5. Change PIN")
    print(Fore.CYAN + "6. Exit")
    return input(Fore.YELLOW + "\nEnter your choice (1-6): ")

def check_balance(user_data):
    print(Fore.GREEN + f"\nYour current balance is: ${user_data["balance"]:.2f}")

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

def deposit(accounts, username, user_data):
    try:
        amount = float(input(Fore.YELLOW + "Enter amount to deposit: $"))
        if amount <= 0:
            print(Fore.RED + "Amount must be positive.")
            return
        user_data["balance"] += amount
        record_transaction(accounts, username, "DEPOSIT", amount)
        print(Fore.GREEN + f"Deposited ${amount:.2f}. New balance: ${user_data["balance"]:.2f}")
    except ValueError:
        print(Fore.RED + "Invalid amount. Please enter a number.")

def withdraw(accounts, username, user_data):
    try:
        amount = float(input(Fore.YELLOW + "Enter amount to withdraw: $"))
        if amount <= 0:
            print(Fore.RED + "Amount must be positive.")
            return
        if amount > user_data["balance"]:
            print(Fore.RED + "Insufficient funds.")
            return
        user_data["balance"] -= amount
        record_transaction(accounts, username, "WITHDRAW", amount)
        print(Fore.GREEN + f"Withdrew ${amount:.2f}. New balance: ${user_data["balance"]:.2f}")
    except ValueError:
        print(Fore.RED + "Invalid amount. Please enter a number.")

def view_history(user_data):
    transactions = user_data.get("transactions", [])
    if not transactions:
        print(Fore.YELLOW + "\nNo transactions yet.")
        return
    print(Fore.CYAN + "\n--- Last 10 Transactions ---")
    for trans in transactions[-10:]:
        colour = Fore.GREEN if trans["type"] == "DEPOSIT" else Fore.RED
        print(f"{trans["time"]}  {colour}{trans["type"]:8}  ${trans["amount"]:.2f}")

def change_pin(accounts, username, user_data):
    print(Fore.CYAN + "\n--- Change PIN ---")
    old_pin = input("Enter current PIN: ")
    if old_pin != user_data["pin"]:
        print(Fore.RED + "Incorrect PIN. Cannot change.")
        return
    new_pin = input("Enter new PIN (4 digits): ")
    if not new_pin.isdigit() or len(new_pin) != 4:
        print(Fore.RED + "PIN must be exactly 4 digits.")
        return
    confirm = input("Confirm new PIN: ")
    if new_pin != confirm:
        print(Fore.RED + "PINs do not match.")
        return
    user_data["pin"] = new_pin
    save_accounts(accounts)
    print(Fore.GREEN + "PIN changed successfully!")

def create_new_account(accounts):
    print(Fore.CYAN + "\n--- Create New Account ---")
    username = input("Choose a username: ").strip().lower()
    if not username:
        print(Fore.RED + "Username cannot be empty.")
        return
    if username in accounts:
        print(Fore.RED + "Username already exists.")
        return
    pin = input("Choose a 4-digit PIN: ")
    if not pin.isdigit() or len(pin) != 4:
        print(Fore.RED + "PIN must be exactly 4 digits.")
        return
    accounts[username] = {
        "pin": pin,
        "balance": 0.0,
        "transactions": []
    }
    save_accounts(accounts)
    print(Fore.GREEN + f"Account {username} created successfully! You can now log in.")

def main():
    clear_screen()
    print_header()
    accounts = load_accounts()

    choice = input(Fore.YELLOW + "Press Enter to log in, or type new to create a new account: ").strip().lower()
    if choice == "new":
        create_new_account(accounts)
        input(Fore.YELLOW + "\nPress Enter to continue to login...")
        clear_screen()
        print_header()

    username, user_data = authenticate(accounts)
    if username is None:
        sys.exit(1)

    while True:
        clear_screen()
        print_header()
        choice = show_menu(username)

        if choice == "1":
            check_balance(user_data)
        elif choice == "2":
            deposit(accounts, username, user_data)
        elif choice == "3":
            withdraw(accounts, username, user_data)
        elif choice == "4":
            view_history(user_data)
        elif choice == "5":
            change_pin(accounts, username, user_data)
        elif choice == "6":
            print(Fore.GREEN + f"\nThank you for using Wyllene ATM, {username}. Goodbye!")
            break
        else:
            print(Fore.RED + "Invalid choice. Please select 1-6.")
        input(Fore.YELLOW + "\nPress Enter to continue...")

if __name__ == "__main__":
    main()
