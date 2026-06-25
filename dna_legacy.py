"""Wyllene Dynasty — DNA Legacy System."""
import random
import sqlite3
from datetime import datetime

class DNALegacy:
    def __init__(self):
        self.db = "dynasty.db"
        self._init()
    
    def _init(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        c.execute("""CREATE TABLE IF NOT EXISTS dna_profiles (
            username TEXT PRIMARY KEY,
            intelligence INTEGER DEFAULT 50,
            charisma INTEGER DEFAULT 50,
            business_acumen INTEGER DEFAULT 50,
            risk_tolerance INTEGER DEFAULT 50,
            longevity INTEGER DEFAULT 50,
            talent TEXT DEFAULT 'Normal',
            bloodline TEXT,
            generation INTEGER DEFAULT 1,
            mutated INTEGER DEFAULT 0
        )""")
        
        c.execute("""CREATE TABLE IF NOT EXISTS bloodlines (
            name TEXT PRIMARY KEY,
            founder TEXT,
            total_generations INTEGER DEFAULT 1,
            total_members INTEGER DEFAULT 1,
            avg_intelligence REAL DEFAULT 50,
            avg_wealth REAL DEFAULT 0,
            signature_trait TEXT,
            founded_year INTEGER
        )""")
        
        c.execute("""CREATE TABLE IF NOT EXISTS mutations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            mutation_name TEXT,
            effect TEXT,
            impact TEXT,
            occurred_year INTEGER
        )""")
        
        conn.commit()
        conn.close()
    
    def generate_dna(self, username, bloodline=None, parent1_dna=None, parent2_dna=None):
        """Generate DNA for a new character."""
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        if parent1_dna and parent2_dna:
            # Inherited — blend parent DNA
            intelligence = (parent1_dna.get('intelligence', 50) + parent2_dna.get('intelligence', 50)) // 2
            charisma = (parent1_dna.get('charisma', 50) + parent2_dna.get('charisma', 50)) // 2
            business = (parent1_dna.get('business_acumen', 50) + parent2_dna.get('business_acumen', 50)) // 2
            risk = (parent1_dna.get('risk_tolerance', 50) + parent2_dna.get('risk_tolerance', 50)) // 2
            longevity = (parent1_dna.get('longevity', 50) + parent2_dna.get('longevity', 50)) // 2
        else:
            # Fresh DNA — random
            intelligence = random.randint(20, 80)
            charisma = random.randint(20, 80)
            business = random.randint(20, 80)
            risk = random.randint(20, 80)
            longevity = random.randint(20, 80)
        
        # Random variation
        intelligence += random.randint(-10, 10)
        charisma += random.randint(-10, 10)
        business += random.randint(-10, 10)
        risk += random.randint(-10, 10)
        longevity += random.randint(-10, 10)
        
        # Clamp values
        intelligence = max(1, min(100, intelligence))
        charisma = max(1, min(100, charisma))
        business = max(1, min(100, business))
        risk = max(1, min(100, risk))
        longevity = max(1, min(100, longevity))
        
        # Determine talent
        avg = (intelligence + charisma + business) // 3
        if avg >= 90:
            talent = random.choice(["Genius 🧠", "Prodigy ⭐", "Savant 🔮"])
        elif avg >= 75:
            talent = random.choice(["Gifted 📚", "Talented 🎯", "Sharp 💡"])
        elif avg >= 60:
            talent = "Capable 👍"
        elif avg >= 40:
            talent = "Normal 👤"
        else:
            talent = random.choice(["Challenged 😔", "Underdog 💪"])
        
        # Chance of mutation
        mutated = random.random() < 0.05
        mutation_name = None
        if mutated:
            mutations = [
                ("Golden Touch", "business_acumen", 20, "📈 Business deals always succeed"),
                ("Silver Tongue", "charisma", 25, "🗣️ Unmatched persuasion ability"),
                ("Iron Will", "risk_tolerance", 20, "🛡️ Immune to market panic"),
                ("Eagle Eye", "intelligence", 20, "👁️ Sees patterns others miss"),
                ("Phoenix Blood", "longevity", 30, "🔥 Lives far beyond normal years"),
                ("Bad Luck Gene", "business_acumen", -15, "💀 Cursed in business"),
            ]
            mutation = random.choice(mutations)
            mutation_name = mutation[0]
            
            c.execute("INSERT INTO mutations (username, mutation_name, effect, impact, occurred_year) VALUES (?,?,?,?,?)",
                      (username, mutation_name, mutation[3], mutation[2], datetime.now().year))
        
        if not bloodline:
            bloodline = f"{username.capitalize()} Bloodline"
            
            c.execute("INSERT INTO bloodlines (name, founder, signature_trait, founded_year) VALUES (?,?,?,?)",
                      (bloodline, username, talent, datetime.now().year))
        
        c.execute("""INSERT OR REPLACE INTO dna_profiles 
                     (username, intelligence, charisma, business_acumen, risk_tolerance, longevity, talent, bloodline, mutated)
                     VALUES (?,?,?,?,?,?,?,?,?)""",
                  (username, intelligence, charisma, business, risk, longevity, talent, bloodline, 1 if mutated else 0))
        
        conn.commit()
        conn.close()
        
        return {
            "intelligence": intelligence,
            "charisma": charisma,
            "business_acumen": business,
            "risk_tolerance": risk,
            "longevity": longevity,
            "talent": talent,
            "bloodline": bloodline,
            "mutated": mutated,
            "mutation": mutation_name
        }
    
    def get_dna(self, username):
        """Get DNA profile for a character."""
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM dna_profiles WHERE username=?", (username,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_bloodline(self, bloodline_name):
        """Get bloodline details."""
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM bloodlines WHERE name=?", (bloodline_name,))
        row = c.fetchone()
        if not row:
            conn.close()
            return None
        
        bloodline = dict(row)
        c.execute("SELECT COUNT(*), AVG(intelligence) FROM dna_profiles WHERE bloodline=?", (bloodline_name,))
        stats = c.fetchone()
        bloodline["total_members"] = stats[0]
        bloodline["avg_intelligence"] = stats[1] or 50
        conn.close()
        return bloodline
    
    def get_all_bloodlines(self):
        """Get all bloodlines ranked."""
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM bloodlines ORDER BY avg_wealth DESC")
        bloodlines = [dict(row) for row in c.fetchall()]
        conn.close()
        return bloodlines

dna = DNALegacy()
