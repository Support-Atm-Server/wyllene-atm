"""Wyllene Dynasty — AI Rival Dynasties."""
import random
import sqlite3
from datetime import datetime

class AIRivals:
    def __init__(self):
        self.db = "dynasty.db"
        self._init()
    
    def _init(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        c.execute("""CREATE TABLE IF NOT EXISTS ai_dynasties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dynasty_name TEXT UNIQUE,
            founder_name TEXT,
            personality TEXT,
            strategy TEXT,
            net_worth REAL DEFAULT 10000000,
            members INTEGER DEFAULT 1,
            businesses INTEGER DEFAULT 0,
            aggression REAL DEFAULT 0.5,
            intelligence REAL DEFAULT 0.5,
            founded_year INTEGER,
            alive INTEGER DEFAULT 1,
            rivalry_with TEXT
        )""")
        
        c.execute("""CREATE TABLE IF NOT EXISTS ai_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dynasty_name TEXT,
            action_type TEXT,
            description TEXT,
            impact REAL,
            year INTEGER
        )""")
        
        c.execute("""CREATE TABLE IF NOT EXISTS dynasty_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dynasty1 TEXT,
            dynasty2 TEXT,
            relation TEXT,
            strength REAL DEFAULT 0.5
        )""")
        
        conn.commit()
        conn.close()
    
    def generate_rival_dynasties(self, count=5):
        """Generate AI rival dynasties."""
        first_names = ["Alexander", "Victoria", "Sebastian", "Isabella", "Maximilian", "Arabella", 
                       "Constantine", "Catherine", "Frederick", "Elizabeth", "Napoleon", "Cleopatra"]
        last_names = ["Blackwood", "Sterling", "Goldcrest", "Ironwood", "Silverton", "Ashford",
                      "Ravensworth", "Montgomery", "Windsor", "Carmichael", "Beaumont", "Kensington"]
        
        personalities = ["Aggressive 🦁", "Conservative 🐢", "Innovative 🚀", "Traditional 🏛️", "Cunning 🦊"]
        strategies = ["Hostile Takeovers", "Slow Growth", "Tech Disruption", "Real Estate Empire", 
                      "Global Expansion", "Monopoly Builder", "Value Investing"]
        
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        created = []
        for _ in range(count):
            founder = f"{random.choice(first_names)} {random.choice(last_names)}"
            dynasty = f"House {random.choice(last_names)}"
            personality = random.choice(personalities)
            strategy = random.choice(strategies)
            net_worth = random.randint(50000000, 500000000)
            
            try:
                c.execute("""INSERT INTO ai_dynasties 
                    (dynasty_name, founder_name, personality, strategy, net_worth, members, businesses, founded_year)
                    VALUES (?,?,?,?,?,?,?,?)""",
                    (dynasty, founder, personality, strategy, net_worth, 
                     random.randint(1, 8), random.randint(1, 5), random.randint(1950, 2020)))
                created.append({"dynasty": dynasty, "founder": founder, "personality": personality, 
                               "net_worth": net_worth, "strategy": strategy})
            except:
                pass
        
        conn.commit()
        conn.close()
        return created
    
    def get_all_rivals(self):
        """Get all AI dynasties."""
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM ai_dynasties WHERE alive=1 ORDER BY net_worth DESC")
        rivals = [dict(row) for row in c.fetchall()]
        conn.close()
        return rivals
    
    def simulate_ai_turn(self, dynasty_name):
        """Simulate one turn for an AI dynasty."""
        actions = [
            {"type": "investment", "desc": "Made strategic investments", "impact": random.randint(-5000000, 15000000)},
            {"type": "acquisition", "desc": "Acquired a competitor", "impact": random.randint(10000000, 50000000)},
            {"type": "expansion", "desc": "Expanded into new markets", "impact": random.randint(5000000, 25000000)},
            {"type": "loss", "desc": "Suffered market losses", "impact": random.randint(-20000000, -2000000)},
            {"type": "innovation", "desc": "Launched innovative product", "impact": random.randint(10000000, 100000000)},
            {"type": "scandal", "desc": "Public scandal damaged reputation", "impact": random.randint(-15000000, -5000000)},
        ]
        
        action = random.choice(actions)
        
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("UPDATE ai_dynasties SET net_worth = net_worth + ? WHERE dynasty_name=?", 
                  (action["impact"], dynasty_name))
        c.execute("INSERT INTO ai_actions (dynasty_name, action_type, description, impact, year) VALUES (?,?,?,?,?)",
                  (dynasty_name, action["type"], action["desc"], action["impact"], datetime.now().year))
        conn.commit()
        conn.close()
        
        return action
    
    def simulate_all_ai_turns(self):
        """Simulate turns for all AI dynasties."""
        rivals = self.get_all_rivals()
        results = []
        for rival in rivals:
            action = self.simulate_ai_turn(rival["dynasty_name"])
            results.append({"dynasty": rival["dynasty_name"], "action": action})
        return results
    
    def get_combined_leaderboard(self, player_dynasties=None):
        """Get combined leaderboard with AI and player dynasties."""
        ai = self.get_all_rivals()
        
        leaderboard = []
        for a in ai:
            leaderboard.append({
                "name": a["dynasty_name"],
                "founder": a["founder_name"],
                "type": "AI",
                "personality": a["personality"],
                "wealth": a["net_worth"],
                "members": a["members"],
                "businesses": a["businesses"]
            })
        
        if player_dynasties:
            for p in player_dynasties:
                leaderboard.append({
                    "name": p.get("dynasty", "Unknown"),
                    "founder": p.get("founder", "Player"),
                    "type": "👑 PLAYER",
                    "personality": "Human",
                    "wealth": p.get("wealth", 0),
                    "members": p.get("members", 1),
                    "businesses": p.get("businesses", 0)
                })
        
        leaderboard.sort(key=lambda x: x["wealth"], reverse=True)
        return leaderboard
    
    def rivalry_event(self, dynasty1, dynasty2):
        """Generate a rivalry event between two dynasties."""
        events = [
            f"⚔️ {dynasty1} and {dynasty2} engage in a hostile takeover battle!",
            f"🤝 {dynasty1} proposes a strategic alliance with {dynasty2}.",
            f"📰 {dynasty1} publicly criticizes {dynasty2}'s business practices.",
            f"💍 A marriage is arranged between {dynasty1} and {dynasty2} heirs!",
            f"🏆 {dynasty1} outbids {dynasty2} for a crucial acquisition.",
        ]
        return random.choice(events)

ai_rivals = AIRivals()
