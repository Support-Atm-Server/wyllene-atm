
"""
Wyllene Dynasty — Generational Wealth Engine
Founded by Lunga Titus Malebadi
© 2026 All Rights Reserved
"""
"""Wyllene Dynasty — Core Life Simulation Engine."""
import sqlite3
import random
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class LifeEvent:
    year: int
    event_type: str
    description: str
    financial_impact: float

class DynastyEngine:
    def __init__(self):
        self.db = "dynasty.db"
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        # Characters
        c.execute("""CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            full_name TEXT,
            age INTEGER DEFAULT 18,
            health INTEGER DEFAULT 100,
            happiness INTEGER DEFAULT 70,
            education TEXT DEFAULT 'High School',
            career TEXT DEFAULT 'Unemployed',
            net_worth REAL DEFAULT 0,
            generation INTEGER DEFAULT 1,
            dynasty_name TEXT,
            alive INTEGER DEFAULT 1,
            birth_year INTEGER,
            spouse TEXT,
            parent_username TEXT
        )""")
        
        # Family tree
        c.execute("""CREATE TABLE IF NOT EXISTS family_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person1 TEXT,
            person2 TEXT,
            relation TEXT,
            since_year INTEGER
        )""")
        
        # Trust funds
        c.execute("""CREATE TABLE IF NOT EXISTS trust_funds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_username TEXT,
            beneficiary TEXT,
            amount REAL,
            unlock_age INTEGER DEFAULT 25,
            conditions TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            active INTEGER DEFAULT 1
        )""")
        
        # Businesses
        c.execute("""CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_username TEXT,
            name TEXT,
            sector TEXT,
            revenue REAL DEFAULT 0,
            expenses REAL DEFAULT 0,
            valuation REAL DEFAULT 0,
            employees INTEGER DEFAULT 1,
            founded_year INTEGER,
            active INTEGER DEFAULT 1
        )""")
        
        # Life events
        c.execute("""CREATE TABLE IF NOT EXISTS life_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            year INTEGER,
            event_type TEXT,
            description TEXT,
            impact REAL DEFAULT 0
        )""")
        
        # Assets (dynasty-specific)
        c.execute("""CREATE TABLE IF NOT EXISTS dynasty_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            asset_type TEXT,
            name TEXT,
            value REAL DEFAULT 0,
            purchase_year INTEGER,
            growth_rate REAL DEFAULT 0.05
        )""")
        
        conn.commit()
        conn.close()
    
    # ---------- CHARACTER CREATION ----------
    def create_character(self, username, full_name, age=18, education="High School", 
                         starting_wealth=10000, dynasty_name="", parent=None):
        """Create a new character in the dynasty."""
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        generation = 1
        if parent:
            c.execute("SELECT generation, dynasty_name FROM characters WHERE username=?", (parent,))
            row = c.fetchone()
            if row:
                generation = row[0] + 1
                if not dynasty_name:
                    dynasty_name = row[1]
        
        birth_year = datetime.now().year - age
        
        try:
            c.execute("""INSERT INTO characters 
                (username, full_name, age, education, net_worth, generation, 
                 dynasty_name, birth_year, parent_username)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (username, full_name, age, education, starting_wealth, generation,
                 dynasty_name, birth_year, parent))
            
            # Add initial cash asset
            c.execute("INSERT INTO dynasty_assets (username, asset_type, name, value, purchase_year) VALUES (?,?,?,?,?)",
                      (username, "Cash", "Checking Account", starting_wealth, datetime.now().year))
            
            # Add life event
            c.execute("INSERT INTO life_events (username, year, event_type, description) VALUES (?,?,?,?)",
                      (username, datetime.now().year, "birth", f"Started life as {full_name}"))
            
            conn.commit()
            return {"status": "ok", "generation": generation, "dynasty": dynasty_name}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()
    
    # ---------- CHARACTER PROFILE ----------
    def get_character(self, username):
        """Get full character profile."""
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM characters WHERE username=?", (username,))
        char = c.fetchone()
        if not char:
            conn.close()
            return None
        
        char_dict = dict(char)
        
        # Get assets
        c.execute("SELECT SUM(value) FROM dynasty_assets WHERE username=?", (username,))
        char_dict["total_assets"] = c.fetchone()[0] or 0
        
        # Get businesses
        c.execute("SELECT COUNT(*), SUM(valuation) FROM businesses WHERE owner_username=? AND active=1", (username,))
        biz = c.fetchone()
        char_dict["business_count"] = biz[0] or 0
        char_dict["business_value"] = biz[1] or 0
        
        # Get trust funds
        c.execute("SELECT COUNT(*), SUM(amount) FROM trust_funds WHERE creator_username=? AND active=1", (username,))
        tf = c.fetchone()
        char_dict["trust_fund_count"] = tf[0] or 0
        char_dict["trust_fund_value"] = tf[1] or 0
        
        # Get children
        c.execute("SELECT username, full_name, age FROM characters WHERE parent_username=?", (username,))
        char_dict["children"] = [dict(row) for row in c.fetchall()]
        
        # Get life events
        c.execute("SELECT * FROM life_events WHERE username=? ORDER BY year DESC LIMIT 10", (username,))
        char_dict["recent_events"] = [dict(row) for row in c.fetchall()]
        
        conn.close()
        return char_dict
    
    # ---------- AGE PROGRESSION ----------
    def advance_year(self, username):
        """Advance character by one year with random events."""
        char = self.get_character(username)
        if not char:
            return {"status": "error", "message": "Character not found"}
        
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        new_age = char["age"] + 1
        events = []
        net_change = 0
        
        # Career income
        career_income = self._get_career_income(char["career"])
        net_change += career_income
        events.append({"type": "career", "desc": f"Earned ${career_income:,} from {char['career']}", "impact": career_income})
        
        # Business income
        c.execute("SELECT SUM(revenue - expenses) FROM businesses WHERE owner_username=? AND active=1", (username,))
        biz_income = c.fetchone()[0] or 0
        if biz_income > 0:
            net_change += biz_income
            events.append({"type": "business", "desc": f"Businesses generated ${biz_income:,}", "impact": biz_income})
        
        # Investment returns
        c.execute("SELECT SUM(value * growth_rate) FROM dynasty_assets WHERE username=? AND asset_type='Stocks'", (username,))
        investment_return = c.fetchone()[0] or 0
        if investment_return > 0:
            net_change += investment_return
            events.append({"type": "investment", "desc": f"Investments returned ${investment_return:,.0f}", "impact": investment_return})
        
        # Random event (10% chance)
        if random.random() < 0.1:
            event = self._random_event(char)
            net_change += event["impact"]
            events.append(event)
        
        # Update character
        c.execute("UPDATE characters SET age=?, net_worth=net_worth+?, happiness=happiness+? WHERE username=?",
                  (new_age, net_change, random.randint(-5, 5), username))
        
        # Record events
        for evt in events:
            c.execute("INSERT INTO life_events (username, year, event_type, description, impact) VALUES (?,?,?,?,?)",
                      (username, datetime.now().year, evt["type"], evt["desc"], evt["impact"]))
        
        conn.commit()
        conn.close()
        
        return {"status": "ok", "new_age": new_age, "events": events, "net_change": net_change}
    
    def _get_career_income(self, career):
        incomes = {
            "Unemployed": 0,
            "Entry Level": 35000,
            "Professional": 75000,
            "Manager": 120000,
            "Executive": 250000,
            "CEO": 500000,
            "Entrepreneur": random.randint(50000, 500000),
            "Investor": random.randint(100000, 1000000),
        }
        return incomes.get(career, 20000) + random.randint(-5000, 20000)
    
    def _random_event(self, char):
        events = [
            {"type": "windfall", "desc": "📈 Stock market boom! Portfolio up.", "impact": random.randint(5000, 50000)},
            {"type": "loss", "desc": "📉 Market dip. Some losses.", "impact": -random.randint(2000, 20000)},
            {"type": "opportunity", "desc": "💡 Business opportunity arose!", "impact": random.randint(10000, 100000)},
            {"type": "scandal", "desc": "📰 Minor scandal. Reputation cost.", "impact": -random.randint(5000, 15000)},
            {"type": "bonus", "desc": "🏆 Performance bonus received!", "impact": random.randint(3000, 30000)},
            {"type": "health", "desc": "🏥 Medical expense.", "impact": -random.randint(1000, 10000)},
        ]
        return random.choice(events)
    
    # ---------- TRUST FUNDS ----------
    def create_trust_fund(self, creator, beneficiary, amount, unlock_age=25, conditions=""):
        """Create a trust fund for a beneficiary."""
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        # Check creator has enough funds
        c.execute("SELECT net_worth FROM characters WHERE username=?", (creator,))
        row = c.fetchone()
        if not row or row[0] < amount:
            conn.close()
            return {"status": "error", "message": "Insufficient funds"}
        
        # Deduct from creator
        c.execute("UPDATE characters SET net_worth = net_worth - ? WHERE username=?", (amount, creator))
        
        # Create trust fund
        c.execute("""INSERT INTO trust_funds (creator_username, beneficiary, amount, unlock_age, conditions)
                     VALUES (?,?,?,?,?)""", (creator, beneficiary, amount, unlock_age, conditions))
        
        # Record event
        c.execute("INSERT INTO life_events (username, year, event_type, description, impact) VALUES (?,?,?,?,?)",
                  (creator, datetime.now().year, "trust_fund", f"Created ${amount:,} trust for {beneficiary}", -amount))
        
        conn.commit()
        conn.close()
        return {"status": "ok", "message": f"Trust fund of ${amount:,} created for {beneficiary}"}
    
    # ---------- BUSINESSES ----------
    def start_business(self, owner, name, sector, initial_investment):
        """Start a new business."""
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        c.execute("SELECT net_worth FROM characters WHERE username=?", (owner,))
        row = c.fetchone()
        if not row or row[0] < initial_investment:
            conn.close()
            return {"status": "error", "message": "Insufficient funds"}
        
        c.execute("UPDATE characters SET net_worth = net_worth - ? WHERE username=?", (initial_investment, owner))
        
        valuation = initial_investment * random.uniform(0.8, 1.5)
        c.execute("""INSERT INTO businesses (owner_username, name, sector, revenue, expenses, valuation, founded_year)
                     VALUES (?,?,?,?,?,?,?)""",
                  (owner, name, sector, 0, 0, valuation, datetime.now().year))
        
        c.execute("INSERT INTO life_events (username, year, event_type, description, impact) VALUES (?,?,?,?,?)",
                  (owner, datetime.now().year, "business", f"Started {name} in {sector}", -initial_investment))
        
        conn.commit()
        conn.close()
        return {"status": "ok", "message": f"Business '{name}' founded with ${initial_investment:,}"}
    
    # ---------- DYNASTY SCORE ----------
    def get_dynasty_score(self, dynasty_name):
        """Calculate total dynasty score."""
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        c.execute("""SELECT SUM(net_worth), COUNT(*), SUM(age)
                     FROM characters WHERE dynasty_name=? AND alive=1""", (dynasty_name,))
        row = c.fetchone()
        
        total_wealth = row[0] or 0
        members = row[1] or 0
        avg_age = row[2] / members if members > 0 else 0
        
        c.execute("SELECT COUNT(*), SUM(valuation) FROM businesses b JOIN characters c ON b.owner_username = c.username WHERE c.dynasty_name=? AND b.active=1", (dynasty_name,))
        biz = c.fetchone()
        biz_count = biz[0] or 0
        biz_value = biz[1] or 0
        
        score = int(total_wealth / 1000) + (members * 500) + int(biz_value / 100) + (biz_count * 1000)
        
        conn.close()
        return {"dynasty": dynasty_name, "total_wealth": total_wealth, "members": members, 
                "businesses": biz_count, "business_value": biz_value, "score": score}

# Global instance
dynasty = DynastyEngine()
