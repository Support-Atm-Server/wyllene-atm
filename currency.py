"""Multi-Currency & Cryptocurrency Module for Wyllene ATM."""
import requests
import json
import sqlite3
from datetime import datetime

# ---------- FIAT CURRENCIES ----------
FIAT_CURRENCIES = {
    "USD": {"symbol": "$", "name": "US Dollar"},
    "EUR": {"symbol": "€", "name": "Euro"},
    "GBP": {"symbol": "£", "name": "British Pound"},
    "JPY": {"symbol": "¥", "name": "Japanese Yen"},
    "ZAR": {"symbol": "R", "name": "South African Rand"},
}

# ---------- CRYPTOCURRENCIES ----------
CRYPTO_CURRENCIES = {
    "BTC": {"symbol": "₿", "name": "Bitcoin", "coingecko_id": "bitcoin"},
    "ETH": {"symbol": "Ξ", "name": "Ethereum", "coingecko_id": "ethereum"},
    "USDT": {"symbol": "₮", "name": "Tether", "coingecko_id": "tether"},
}

class CurrencyManager:
    def __init__(self):
        self.db_file = "atm.db"
        self._init_tables()
    
    def _init_tables(self):
        """Create currency tables."""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # Multi-currency balances per user
        c.execute("""CREATE TABLE IF NOT EXISTS currency_balances (
            username TEXT, currency TEXT, balance REAL DEFAULT 0.0,
            PRIMARY KEY (username, currency))""")
        
        # Crypto balances
        c.execute("""CREATE TABLE IF NOT EXISTS crypto_balances (
            username TEXT, currency TEXT, balance REAL DEFAULT 0.0,
            PRIMARY KEY (username, currency))""")
        
        # Currency transactions
        c.execute("""CREATE TABLE IF NOT EXISTS currency_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT, from_currency TEXT, to_currency TEXT,
            from_amount REAL, to_amount REAL, rate REAL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP)""")
        
        # Crypto transactions
        c.execute("""CREATE TABLE IF NOT EXISTS crypto_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT, currency TEXT, type TEXT,
            amount REAL, price_usd REAL, total_usd REAL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP)""")
        
        conn.commit()
        conn.close()
    
    def get_fiat_rates(self):
        """Get live fiat exchange rates (USD base)."""
        try:
            url = "https://open.er-api.com/v6/latest/USD"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if data.get("result") == "success":
                return data["rates"]
        except:
            pass
        
        # Fallback rates
        return {"USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 149.5, "ZAR": 18.3}
    
    def get_crypto_prices(self):
        """Get live cryptocurrency prices in USD."""
        try:
            ids = ",".join([c["coingecko_id"] for c in CRYPTO_CURRENCIES.values()])
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            
            prices = {}
            for code, info in CRYPTO_CURRENCIES.items():
                cg_id = info["coingecko_id"]
                prices[code] = data.get(cg_id, {}).get("usd", 0)
            return prices
        except:
            # Fallback prices
            return {"BTC": 67500, "ETH": 3450, "USDT": 1.0}
    
    def get_user_fiat_balances(self, username):
        """Get all fiat balances for a user."""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT currency, balance FROM currency_balances WHERE username=?", (username,))
        balances = {row[0]: row[1] for row in c.fetchall()}
        conn.close()
        
        # Ensure default USD balance from main account
        if "USD" not in balances:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute("SELECT balance FROM users WHERE username=?", (username,))
            row = c.fetchone()
            if row:
                balances["USD"] = row[0]
            conn.close()
        
        return balances
    
    def get_user_crypto_balances(self, username):
        """Get all crypto balances for a user."""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT currency, balance FROM crypto_balances WHERE username=?", (username,))
        balances = {row[0]: row[1] for row in c.fetchall()}
        conn.close()
        return balances
    
    def convert_fiat(self, username, from_currency, to_currency, amount):
        """Convert between fiat currencies."""
        if amount <= 0:
            return {"status": "error", "message": "Invalid amount"}
        
        rates = self.get_fiat_rates()
        if from_currency not in rates or to_currency not in rates:
            return {"status": "error", "message": "Unsupported currency"}
        
        # Convert to USD first, then to target
        usd_amount = amount / rates[from_currency]
        converted = usd_amount * rates[to_currency]
        rate = rates[to_currency] / rates[from_currency]
        
        # Update balances
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # Deduct from source
        c.execute("""INSERT INTO currency_balances (username, currency, balance) 
                     VALUES (?,?,?) ON CONFLICT(username, currency) 
                     DO UPDATE SET balance = balance - ?""",
                  (username, from_currency, -amount, amount))
        
        # Add to target
        c.execute("""INSERT INTO currency_balances (username, currency, balance) 
                     VALUES (?,?,?) ON CONFLICT(username, currency) 
                     DO UPDATE SET balance = balance + ?""",
                  (username, to_currency, converted, converted))
        
        # Record transaction
        c.execute("""INSERT INTO currency_transactions 
                     (username, from_currency, to_currency, from_amount, to_amount, rate)
                     VALUES (?,?,?,?,?,?)""",
                  (username, from_currency, to_currency, amount, converted, rate))
        
        conn.commit()
        conn.close()
        
        return {
            "status": "ok",
            "from_amount": amount,
            "from_currency": from_currency,
            "to_amount": round(converted, 2),
            "to_currency": to_currency,
            "rate": round(rate, 4)
        }
    
    def buy_crypto(self, username, crypto, usd_amount):
        """Buy cryptocurrency using USD."""
        if usd_amount <= 0:
            return {"status": "error", "message": "Invalid amount"}
        
        prices = self.get_crypto_prices()
        if crypto not in prices:
            return {"status": "error", "message": "Unsupported crypto"}
        
        price = prices[crypto]
        crypto_amount = usd_amount / price
        
        # Check USD balance
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE username=?", (username,))
        row = c.fetchone()
        if not row or row[0] < usd_amount:
            conn.close()
            return {"status": "error", "message": "Insufficient USD balance"}
        
        # Deduct USD
        c.execute("UPDATE users SET balance = balance - ? WHERE username=?", (usd_amount, username))
        
        # Add crypto
        c.execute("""INSERT INTO crypto_balances (username, currency, balance) 
                     VALUES (?,?,?) ON CONFLICT(username, currency) 
                     DO UPDATE SET balance = balance + ?""",
                  (username, crypto, crypto_amount, crypto_amount))
        
        # Record transaction
        c.execute("""INSERT INTO crypto_transactions (username, currency, type, amount, price_usd, total_usd)
                     VALUES (?,?,?,?,?,?)""",
                  (username, crypto, "BUY", crypto_amount, price, usd_amount))
        
        conn.commit()
        conn.close()
        
        return {
            "status": "ok",
            "crypto": crypto,
            "amount": round(crypto_amount, 6),
            "price": price,
            "total_usd": usd_amount
        }
    
    def sell_crypto(self, username, crypto, crypto_amount):
        """Sell cryptocurrency for USD."""
        if crypto_amount <= 0:
            return {"status": "error", "message": "Invalid amount"}
        
        prices = self.get_crypto_prices()
        if crypto not in prices:
            return {"status": "error", "message": "Unsupported crypto"}
        
        price = prices[crypto]
        usd_amount = crypto_amount * price
        
        # Check crypto balance
        balances = self.get_user_crypto_balances(username)
        if crypto not in balances or balances[crypto] < crypto_amount:
            return {"status": "error", "message": "Insufficient crypto balance"}
        
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # Deduct crypto
        c.execute("UPDATE crypto_balances SET balance = balance - ? WHERE username=? AND currency=?",
                  (crypto_amount, username, crypto))
        
        # Add USD
        c.execute("UPDATE users SET balance = balance + ? WHERE username=?", (usd_amount, username))
        
        # Record transaction
        c.execute("""INSERT INTO crypto_transactions (username, currency, type, amount, price_usd, total_usd)
                     VALUES (?,?,?,?,?,?)""",
                  (username, crypto, "SELL", crypto_amount, price, usd_amount))
        
        conn.commit()
        conn.close()
        
        return {
            "status": "ok",
            "crypto": crypto,
            "amount": crypto_amount,
            "price": price,
            "total_usd": round(usd_amount, 2)
        }

# Global instance
currency_mgr = CurrencyManager()
