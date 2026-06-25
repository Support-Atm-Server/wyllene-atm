"""Wyllene Dynasty — Market Cycles, IPOs, Stock Market."""
import sqlite3
import random
from datetime import datetime

class MarketEconomy:
    def __init__(self):
        self.db = "dynasty.db"
        self._init()
    
    def _init(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        # Market state
        c.execute("""CREATE TABLE IF NOT EXISTS market_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER UNIQUE,
            market_type TEXT DEFAULT 'Normal',
            growth_rate REAL DEFAULT 0.05,
            volatility TEXT DEFAULT 'Medium',
            description TEXT
        )""")
        
        # Public companies (IPO'd)
        c.execute("""CREATE TABLE IF NOT EXISTS public_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            ticker TEXT UNIQUE,
            sector TEXT,
            share_price REAL,
            total_shares INTEGER,
            ipo_year INTEGER,
            founder_username TEXT
        )""")
        
        # Stock portfolios
        c.execute("""CREATE TABLE IF NOT EXISTS stock_portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            ticker TEXT,
            shares INTEGER,
            avg_price REAL,
            purchased_year INTEGER
        )""")
        
        # Economic events log
        c.execute("""CREATE TABLE IF NOT EXISTS economic_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            event_name TEXT,
            description TEXT,
            impact TEXT,
            sectors_affected TEXT
        )""")
        
        # Dynasty leaderboard cache
        c.execute("""CREATE TABLE IF NOT EXISTS dynasty_leaderboard (
            dynasty_name TEXT PRIMARY KEY,
            total_wealth REAL,
            total_members INTEGER,
            total_businesses INTEGER,
            score INTEGER,
            last_updated TEXT
        )""")
        
        conn.commit()
        conn.close()
    
    # ---------- MARKET CYCLES ----------
    def generate_market_year(self, year=None):
        """Generate market conditions for a year."""
        if not year:
            year = datetime.now().year
        
        market_types = ["Boom 🚀", "Growth 📈", "Normal 📊", "Correction 📉", "Recession 📉", "Depression 💀"]
        weights = [10, 25, 40, 15, 8, 2]
        market = random.choices(market_types, weights=weights)[0]
        
        rates = {"Boom 🚀": 0.20, "Growth 📈": 0.12, "Normal 📊": 0.06, "Correction 📉": -0.05, "Recession 📉": -0.15, "Depression 💀": -0.30}
        volatility = {"Boom 🚀": "High", "Growth 📈": "Medium", "Normal 📊": "Low", "Correction 📉": "High", "Recession 📉": "Very High", "Depression 💀": "Extreme"}
        
        rate = rates.get(market, 0.05)
        vol = volatility.get(market, "Medium")
        
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO market_state (year, market_type, growth_rate, volatility) VALUES (?,?,?,?)",
                  (year, market, rate, vol))
        conn.commit()
        conn.close()
        
        return {"year": year, "market": market, "growth": rate, "volatility": vol}
    
    def get_market_state(self, year=None):
        """Get current market state."""
        if not year:
            year = datetime.now().year
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM market_state WHERE year=?", (year,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else self.generate_market_year(year)
    
    # ---------- ECONOMIC EVENTS ----------
    def trigger_economic_event(self, year=None):
        """Trigger a random economic event."""
        if not year:
            year = datetime.now().year
        
        events = [
            {"name": "Tech Boom", "desc": "Technology sector surges!", "impact": "Positive", "sectors": "Tech"},
            {"name": "Oil Crisis", "desc": "Oil prices spike globally.", "impact": "Negative", "sectors": "Energy, Transport"},
            {"name": "Housing Bubble", "desc": "Real estate prices soar then crash.", "impact": "Mixed", "sectors": "Real Estate"},
            {"name": "Trade War", "desc": "International tariffs disrupt markets.", "impact": "Negative", "sectors": "All"},
            {"name": "Innovation Breakthrough", "desc": "New technology transforms industries.", "impact": "Positive", "sectors": "Tech, Healthcare"},
            {"name": "Global Pandemic", "desc": "Worldwide health crisis hits economy.", "impact": "Negative", "sectors": "Travel, Hospitality"},
            {"name": "Green Revolution", "desc": "Renewable energy investment soars.", "impact": "Positive", "sectors": "Energy, Tech"},
            {"name": "Banking Crisis", "desc": "Major banks face liquidity issues.", "impact": "Negative", "sectors": "Finance"},
        ]
        
        event = random.choice(events)
        
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("INSERT INTO economic_events (year, event_name, description, impact, sectors_affected) VALUES (?,?,?,?,?)",
                  (year, event["name"], event["desc"], event["impact"], event["sectors"]))
        conn.commit()
        conn.close()
        
        return event
    
    # ---------- IPO SYSTEM ----------
    def ipo_company(self, founder, business_name, ticker, sector, share_price, total_shares):
        """Take a company public via IPO."""
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        # Check business exists
        c.execute("SELECT * FROM businesses WHERE owner_username=? AND name=? AND active=1", (founder, business_name))
        biz = c.fetchone()
        if not biz:
            conn.close()
            return {"status": "error", "message": "Business not found"}
        
        # Calculate IPO proceeds
        ipo_proceeds = share_price * total_shares
        founder_shares = int(total_shares * 0.4)  # Founder keeps 40%
        public_shares = total_shares - founder_shares
        
        try:
            c.execute("INSERT INTO public_companies (name, ticker, sector, share_price, total_shares, ipo_year, founder_username) VALUES (?,?,?,?,?,?,?)",
                      (business_name, ticker, sector, share_price, public_shares, datetime.now().year, founder))
            
            # Founder gets shares and cash
            c.execute("UPDATE characters SET net_worth = net_worth + ? WHERE username=?", (ipo_proceeds * 0.6, founder))
            c.execute("INSERT INTO stock_portfolio (username, ticker, shares, avg_price, purchased_year) VALUES (?,?,?,?,?)",
                      (founder, ticker, founder_shares, share_price, datetime.now().year))
            
            # Deactivate private business
            c.execute("UPDATE businesses SET active=0 WHERE owner_username=? AND name=?", (founder, business_name))
            
            conn.commit()
            return {"status": "ok", "message": f"🎉 {business_name} (${ticker}) IPO'd! Raised ${ipo_proceeds:,}. You retained {founder_shares} shares."}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()
    
    # ---------- STOCK MARKET ----------
    def buy_stocks(self, username, ticker, shares):
        """Buy shares of a public company."""
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        c.execute("SELECT share_price FROM public_companies WHERE ticker=?", (ticker,))
        row = c.fetchone()
        if not row:
            conn.close()
            return {"status": "error", "message": "Stock not found"}
        
        price = row[0]
        cost = price * shares
        
        c.execute("SELECT net_worth FROM characters WHERE username=?", (username,))
        nw = c.fetchone()
        if not nw or nw[0] < cost:
            conn.close()
            return {"status": "error", "message": "Insufficient funds"}
        
        c.execute("UPDATE characters SET net_worth = net_worth - ? WHERE username=?", (cost, username))
        c.execute("INSERT INTO stock_portfolio (username, ticker, shares, avg_price, purchased_year) VALUES (?,?,?,?,?)",
                  (username, ticker, shares, price, datetime.now().year))
        
        conn.commit()
        conn.close()
        return {"status": "ok", "message": f"📈 Bought {shares} shares of {ticker} at ${price:,.2f} each. Total: ${cost:,.2f}"}
    
    def get_stock_prices(self):
        """Get current stock prices (with market influence)."""
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        market = self.get_market_state()
        growth = market["growth"]
        
        c.execute("SELECT * FROM public_companies")
        stocks = []
        for row in c.fetchall():
            # Apply market growth + random variation
            new_price = row[3] * (1 + growth + random.uniform(-0.05, 0.05))
            c.execute("UPDATE public_companies SET share_price=? WHERE ticker=?", (new_price, row[2]))
            stocks.append({"name": row[1], "ticker": row[2], "sector": row[3], "price": round(new_price, 2)})
        
        conn.commit()
        conn.close()
        return stocks
    
    # ---------- DYNASTY LEADERBOARD ----------
    def update_leaderboard(self):
        """Update the dynasty leaderboard."""
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        c.execute("""SELECT dynasty_name, SUM(net_worth), COUNT(*)
                     FROM characters WHERE alive=1 AND dynasty_name != ''
                     GROUP BY dynasty_name ORDER BY SUM(net_worth) DESC""")
        
        leaderboard = []
        for row in c.fetchall():
            c.execute("SELECT COUNT(*) FROM businesses b JOIN characters c ON b.owner_username = c.username WHERE c.dynasty_name=? AND b.active=1", (row[0],))
            biz_count = c.fetchone()[0] or 0
            
            score = int((row[1] or 0) / 1000) + (row[2] * 500) + (biz_count * 1000)
            
            c.execute("""INSERT OR REPLACE INTO dynasty_leaderboard (dynasty_name, total_wealth, total_members, total_businesses, score, last_updated)
                         VALUES (?,?,?,?,?,?)""",
                      (row[0], row[1] or 0, row[2], biz_count, score, datetime.now().strftime("%Y-%m-%d")))
            
            leaderboard.append({"dynasty": row[0], "wealth": row[1] or 0, "members": row[2], "businesses": biz_count, "score": score})
        
        conn.commit()
        conn.close()
        return leaderboard

# Global instance
economy = MarketEconomy()
