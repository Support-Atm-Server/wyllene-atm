"""Wyllene Dynasty — Family, Heirs & Generational Transfer."""
import sqlite3
import random
from datetime import datetime

class FamilyLegacy:
    def __init__(self):
        self.db = "dynasty.db"
        self._init()
    
    def _init(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        # Marriages
        c.execute("""CREATE TABLE IF NOT EXISTS marriages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person1 TEXT,
            person2 TEXT,
            marriage_year INTEGER,
            divorce_year INTEGER DEFAULT NULL,
            prenup_active INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1
        )""")
        
        # Children (more detailed)
        c.execute("""CREATE TABLE IF NOT EXISTS children (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent1 TEXT,
            parent2 TEXT DEFAULT NULL,
            child_username TEXT UNIQUE,
            full_name TEXT,
            birth_year INTEGER,
            gender TEXT DEFAULT 'unknown',
            education TEXT DEFAULT 'None',
            talent TEXT DEFAULT 'Normal',
            inheritance_share REAL DEFAULT 0.0
        )""")
        
        # Education institutions
        c.execute("""CREATE TABLE IF NOT EXISTS education (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_username TEXT,
            institution TEXT,
            degree TEXT,
            cost REAL DEFAULT 0,
            graduation_year INTEGER,
            completed INTEGER DEFAULT 1
        )""")
        
        # Inheritance records
        c.execute("""CREATE TABLE IF NOT EXISTS inheritance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deceased_username TEXT,
            heir_username TEXT,
            amount REAL,
            asset_type TEXT,
            transfer_year INTEGER
        )""")
        
        # Family milestones
        c.execute("""CREATE TABLE IF NOT EXISTS family_milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dynasty_name TEXT,
            milestone TEXT,
            year INTEGER,
            description TEXT
        )""")
        
        conn.commit()
        conn.close()
    
    # ---------- MARRIAGE ----------
    def marry(self, person1, person2, prenup_amount=0):
        """Marry two characters."""
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        # Check both exist
        c.execute("SELECT username FROM characters WHERE username=? AND alive=1", (person1,))
        if not c.fetchone():
            conn.close()
            return {"status": "error", "message": f"{person1} not found or deceased"}
        
        c.execute("SELECT username FROM characters WHERE username=? AND alive=1", (person2,))
        if not c.fetchone():
            conn.close()
            return {"status": "error", "message": f"{person2} not found or deceased"}
        
        # Check if already married
        c.execute("SELECT * FROM marriages WHERE (person1=? OR person2=?) AND active=1", (person1, person1))
        if c.fetchone():
            conn.close()
            return {"status": "error", "message": f"{person1} is already married"}
        
        year = datetime.now().year
        c.execute("""INSERT INTO marriages (person1, person2, marriage_year, prenup_active)
                     VALUES (?,?,?,?)""", (person1, person2, year, 1 if prenup_amount > 0 else 0))
        
        # Update characters
        c.execute("UPDATE characters SET spouse=? WHERE username=?", (person2, person1))
        c.execute("UPDATE characters SET spouse=? WHERE username=?", (person1, person2))
        
        # Combine assets partially
        if prenup_amount == 0:
            c.execute("SELECT net_worth FROM characters WHERE username=?", (person1,))
            nw1 = c.fetchone()[0] or 0
            c.execute("SELECT net_worth FROM characters WHERE username=?", (person2,))
            nw2 = c.fetchone()[0] or 0
            shared = (nw1 + nw2) * 0.1
            c.execute("UPDATE characters SET net_worth = net_worth + ? WHERE username=?", (shared, person1))
        
        c.execute("INSERT INTO life_events (username, year, event_type, description) VALUES (?,?,?,?)",
                  (person1, year, "marriage", f"Married {person2}"))
        c.execute("INSERT INTO life_events (username, year, event_type, description) VALUES (?,?,?,?)",
                  (person2, year, "marriage", f"Married {person1}"))
        
        conn.commit()
        conn.close()
        return {"status": "ok", "message": f"💒 {person1} and {person2} are now married! Prenup: {'Yes' if prenup_amount > 0 else 'No'}"}
    
    # ---------- CHILDREN ----------
    def have_child(self, parent1, parent2, full_name, gender=None):
        """Have a child."""
        if not gender:
            gender = random.choice(["Male", "Female"])
        
        talents = ["Genius", "Athletic", "Artistic", "Entrepreneurial", "Musical", "Normal"]
        talent = random.choices(talents, weights=[5, 10, 10, 8, 5, 62])[0]
        
        child_username = full_name.lower().replace(" ", "_")
        birth_year = datetime.now().year
        
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        # Create child character
        c.execute("""SELECT dynasty_name, generation FROM characters WHERE username=?""", (parent1,))
        row = c.fetchone()
        dynasty_name = row[0] if row else ""
        generation = row[1] + 1 if row else 2
        
        try:
            c.execute("""INSERT INTO characters (username, full_name, age, education, net_worth, generation, dynasty_name, birth_year, parent_username)
                         VALUES (?,?,0,'None',0,?,?,?,?)""",
                      (child_username, full_name, generation, dynasty_name, birth_year, parent1))
            
            c.execute("""INSERT INTO children (parent1, parent2, child_username, full_name, birth_year, gender, talent)
                         VALUES (?,?,?,?,?,?,?)""",
                      (parent1, parent2, child_username, full_name, birth_year, gender, talent))
            
            c.execute("INSERT INTO life_events (username, year, event_type, description) VALUES (?,?,?,?)",
                      (parent1, birth_year, "child", f"Welcomed {full_name} ({gender})"))
            
            conn.commit()
            return {"status": "ok", "message": f"👶 {full_name} born! Gender: {gender}, Talent: {talent}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()
    
    # ---------- EDUCATION ----------
    def send_to_school(self, child_username, institution, degree, cost):
        """Send a child to school."""
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        c.execute("SELECT parent_username FROM characters WHERE username=?", (child_username,))
        row = c.fetchone()
        if not row:
            conn.close()
            return {"status": "error", "message": "Child not found"}
        
        parent = row[0]
        c.execute("SELECT net_worth FROM characters WHERE username=?", (parent,))
        nw = c.fetchone()
        if not nw or nw[0] < cost:
            conn.close()
            return {"status": "error", "message": "Insufficient funds for education"}
        
        c.execute("UPDATE characters SET net_worth = net_worth - ? WHERE username=?", (cost, parent))
        
        grad_year = datetime.now().year + random.randint(2, 4)
        c.execute("""INSERT INTO education (child_username, institution, degree, cost, graduation_year)
                     VALUES (?,?,?,?,?)""", (child_username, institution, degree, cost, grad_year))
        
        c.execute("UPDATE children SET education=? WHERE child_username=?", (f"{degree} at {institution}", child_username))
        c.execute("UPDATE characters SET education=? WHERE username=?", (degree, child_username))
        
        conn.commit()
        conn.close()
        return {"status": "ok", "message": f"🎓 {child_username} enrolled at {institution} for {degree} (${cost:,})"}
    
    # ---------- INHERITANCE ----------
    def process_inheritance(self, deceased_username):
        """Distribute assets to heirs upon death."""
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        # Get estate plan
        c.execute("SELECT * FROM estate_plans WHERE username=? AND will_active=1", (deceased_username,))
        will = c.fetchone()
        
        # Get total net worth
        c.execute("SELECT net_worth FROM characters WHERE username=?", (deceased_username,))
        row = c.fetchone()
        total_estate = row[0] if row else 0
        
        # Get children/heirs
        c.execute("SELECT child_username FROM children WHERE parent1=? OR parent2=?", (deceased_username, deceased_username))
        heirs = [row[0] for row in c.fetchall()]
        
        if not heirs:
            # No heirs — wealth goes to charity
            c.execute("UPDATE characters SET alive=0, net_worth=0 WHERE username=?", (deceased_username,))
            conn.commit()
            conn.close()
            return {"status": "ok", "message": f"${total_estate:,} donated to charity. No heirs found."}
        
        # Distribute equally
        share = total_estate / len(heirs)
        year = datetime.now().year
        
        for heir in heirs:
            c.execute("UPDATE characters SET net_worth = net_worth + ? WHERE username=?", (share, heir))
            c.execute("""INSERT INTO inheritance (deceased_username, heir_username, amount, asset_type, transfer_year)
                         VALUES (?,?,?,?,?)""", (deceased_username, heir, share, "Cash", year))
            c.execute("INSERT INTO life_events (username, year, event_type, description) VALUES (?,?,?,?)",
                      (heir, year, "inheritance", f"Inherited ${share:,.0f} from {deceased_username}"))
        
        # Deactivate deceased
        c.execute("UPDATE characters SET alive=0, net_worth=0 WHERE username=?", (deceased_username,))
        
        conn.commit()
        conn.close()
        return {"status": "ok", "message": f"⚰️ Estate distributed: ${total_estate:,} split among {len(heirs)} heirs"}
    
    # ---------- FAMILY TREE ----------
    def get_family_tree(self, username):
        """Get family tree for a character."""
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM characters WHERE username=?", (username,))
        char = c.fetchone()
        if not char:
            conn.close()
            return None
        
        tree = {
            "character": dict(char),
            "spouse": None,
            "parents": [],
            "children": [],
            "siblings": []
        }
        
        # Spouse
        if char["spouse"]:
            c.execute("SELECT * FROM characters WHERE username=?", (char["spouse"],))
            spouse = c.fetchone()
            if spouse:
                tree["spouse"] = dict(spouse)
        
        # Children
        c.execute("SELECT * FROM children WHERE parent1=? OR parent2=?", (username, username))
        tree["children"] = [dict(row) for row in c.fetchall()]
        
        # Parents
        if char["parent_username"]:
            c.execute("SELECT * FROM characters WHERE username=?", (char["parent_username"],))
            parent = c.fetchone()
            if parent:
                tree["parents"].append(dict(parent))
        
        conn.close()
        return tree

# Global instance
family = FamilyLegacy()
