"""Wyllene Dynasty — Asset Protection & Legal Shield."""
import sqlite3
import random
from datetime import datetime

class AssetProtection:
    def __init__(self):
        self.db = "dynasty.db"
        self._init()
    
    def _init(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        # LLCs / Holding Companies
        c.execute("""CREATE TABLE IF NOT EXISTS holding_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_username TEXT,
            company_name TEXT,
            jurisdiction TEXT,
            assets_under REAL DEFAULT 0,
            annual_fee REAL DEFAULT 500,
            founded_year INTEGER,
            active INTEGER DEFAULT 1
        )""")
        
        # Offshore trusts
        c.execute("""CREATE TABLE IF NOT EXISTS offshore_trusts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_username TEXT,
            trust_name TEXT,
            jurisdiction TEXT,
            amount REAL DEFAULT 0,
            tax_rate REAL DEFAULT 0.0,
            privacy_level TEXT DEFAULT 'High',
            created_year INTEGER,
            active INTEGER DEFAULT 1
        )""")
        
        # Insurance policies
        c.execute("""CREATE TABLE IF NOT EXISTS insurance_policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            policy_type TEXT,
            coverage REAL,
            premium REAL,
            provider TEXT,
            active INTEGER DEFAULT 1
        )""")
        
        # Wills & estate plans
        c.execute("""CREATE TABLE IF NOT EXISTS estate_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            will_active INTEGER DEFAULT 0,
            executor TEXT,
            beneficiaries TEXT,
            estate_tax_optimized INTEGER DEFAULT 0,
            last_updated TEXT
        )""")
        
        # Pre-nuptial agreements
        c.execute("""CREATE TABLE IF NOT EXISTS prenups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person1 TEXT,
            person2 TEXT,
            assets_protected REAL,
            signed_date TEXT,
            active INTEGER DEFAULT 1
        )""")
        
        # Family constitution
        c.execute("""CREATE TABLE IF NOT EXISTS family_constitution (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dynasty_name TEXT UNIQUE,
            voting_rights TEXT,
            inheritance_rules TEXT,
            business_succession TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        
        # Charitable foundations
        c.execute("""CREATE TABLE IF NOT EXISTS foundations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            founder_username TEXT,
            foundation_name TEXT,
            endowed_amount REAL,
            tax_deduction REAL,
            founded_year INTEGER,
            active INTEGER DEFAULT 1
        )""")
        
        conn.commit()
        conn.close()
    
    # ---------- LLC / HOLDING COMPANY ----------
    def create_llc(self, owner, company_name, jurisdiction="Delaware", initial_assets=0):
        """Create a holding company to protect assets."""
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        c.execute("""INSERT INTO holding_companies (owner_username, company_name, jurisdiction, assets_under, founded_year)
                     VALUES (?,?,?,?,?)""",
                  (owner, company_name, jurisdiction, initial_assets, datetime.now().year))
        
        # Transfer assets from personal to LLC (protection!)
        if initial_assets > 0:
            c.execute("UPDATE characters SET net_worth = net_worth - ? WHERE username=?", (initial_assets, owner))
        
        conn.commit()
        conn.close()
        return {"status": "ok", "message": f"LLC '{company_name}' formed in {jurisdiction}. Assets protected: ${initial_assets:,}"}
    
    def get_llcs(self, owner):
        """Get all holding companies for an owner."""
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM holding_companies WHERE owner_username=? AND active=1", (owner,))
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return rows
    
    # ---------- OFFSHORE TRUST ----------
    def create_offshore_trust(self, creator, trust_name, jurisdiction="Cayman Islands", amount=0):
        """Create an offshore trust for maximum privacy."""
        jurisdictions = {
            "Cayman Islands": {"tax": 0.0, "privacy": "Maximum"},
            "Switzerland": {"tax": 0.5, "privacy": "Maximum"},
            "Singapore": {"tax": 0.0, "privacy": "High"},
            "Liechtenstein": {"tax": 0.3, "privacy": "Maximum"},
            "Dubai": {"tax": 0.0, "privacy": "High"},
        }
        
        j_info = jurisdictions.get(jurisdiction, {"tax": 0.0, "privacy": "High"})
        
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        c.execute("""INSERT INTO offshore_trusts (creator_username, trust_name, jurisdiction, amount, tax_rate, privacy_level, created_year)
                     VALUES (?,?,?,?,?,?,?)""",
                  (creator, trust_name, jurisdiction, amount, j_info["tax"], j_info["privacy"], datetime.now().year))
        
        if amount > 0:
            c.execute("UPDATE characters SET net_worth = net_worth - ? WHERE username=?", (amount, creator))
        
        conn.commit()
        conn.close()
        return {"status": "ok", "message": f"Offshore trust '{trust_name}' created in {jurisdiction}. Tax rate: {j_info['tax']}%"}
    
    # ---------- INSURANCE ----------
    def buy_insurance(self, username, policy_type, coverage):
        """Purchase insurance to protect assets."""
        premiums = {
            "Liability": 0.01,
            "Property": 0.008,
            "Life": 0.005,
            "Cyber": 0.012,
            "Directors & Officers": 0.015,
        }
        
        rate = premiums.get(policy_type, 0.01)
        premium = coverage * rate
        
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        c.execute("""INSERT INTO insurance_policies (username, policy_type, coverage, premium, provider)
                     VALUES (?,?,?,?,?)""",
                  (username, policy_type, coverage, premium, "Wyllene Insurance Group"))
        
        c.execute("UPDATE characters SET net_worth = net_worth - ? WHERE username=?", (premium, username))
        
        conn.commit()
        conn.close()
        return {"status": "ok", "message": f"{policy_type} insurance: ${coverage:,} coverage. Premium: ${premium:,.2f}/year"}
    
    # ---------- ESTATE PLAN ----------
    def create_will(self, username, executor, beneficiaries, optimize_tax=True):
        """Create a will and estate plan."""
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        tax_savings = 0
        if optimize_tax:
            # Simulate estate tax savings
            c.execute("SELECT net_worth FROM characters WHERE username=?", (username,))
            row = c.fetchone()
            if row and row[0] > 12000000:
                tax_savings = row[0] * 0.15  # Save ~15% via optimization
        
        c.execute("""INSERT OR REPLACE INTO estate_plans (username, will_active, executor, beneficiaries, estate_tax_optimized, last_updated)
                     VALUES (?,1,?,?,?,?)""",
                  (username, executor, beneficiaries, 1 if optimize_tax else 0, datetime.now().strftime("%Y-%m-%d")))
        
        conn.commit()
        conn.close()
        return {"status": "ok", "message": f"Will created. Executor: {executor}. Tax savings: ${tax_savings:,.0f}"}
    
    # ---------- PRE-NUP ----------
    def sign_prenup(self, person1, person2, assets_protected):
        """Sign a pre-nuptial agreement before marriage."""
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        c.execute("""INSERT INTO prenups (person1, person2, assets_protected, signed_date)
                     VALUES (?,?,?,?)""",
                  (person1, person2, assets_protected, datetime.now().strftime("%Y-%m-%d")))
        
        conn.commit()
        conn.close()
        return {"status": "ok", "message": f"Pre-nup signed protecting ${assets_protected:,} in assets."}
    
    # ---------- FAMILY CONSTITUTION ----------
    def create_family_constitution(self, dynasty_name, voting_rights, inheritance_rules, business_succession):
        """Create a family governance constitution."""
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        c.execute("""INSERT OR REPLACE INTO family_constitution (dynasty_name, voting_rights, inheritance_rules, business_succession)
                     VALUES (?,?,?,?)""",
                  (dynasty_name, voting_rights, inheritance_rules, business_succession))
        
        conn.commit()
        conn.close()
        return {"status": "ok", "message": f"Family constitution created for the {dynasty_name} dynasty."}
    
    # ---------- CHARITABLE FOUNDATION ----------
    def create_foundation(self, founder, foundation_name, endowed_amount):
        """Create a charitable foundation (tax-deductible)."""
        tax_deduction = endowed_amount * 0.30  # 30% tax deduction
        
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        
        c.execute("""INSERT INTO foundations (founder_username, foundation_name, endowed_amount, tax_deduction, founded_year)
                     VALUES (?,?,?,?,?)""",
                  (founder, foundation_name, endowed_amount, tax_deduction, datetime.now().year))
        
        c.execute("UPDATE characters SET net_worth = net_worth - ? WHERE username=?", (endowed_amount, founder))
        
        conn.commit()
        conn.close()
        return {"status": "ok", "message": f"Foundation '{foundation_name}' created. Tax deduction: ${tax_deduction:,.0f}"}
    
    # ---------- PROTECTION SUMMARY ----------
    def get_protection_summary(self, username):
        """Get full protection overview for a client."""
        summary = {
            "llcs": self.get_llcs(username),
            "protected_assets": sum(llc["assets_under"] for llc in self.get_llcs(username)),
            "protection_score": min(100, len(self.get_llcs(username)) * 20),
        }
        return summary

# Global instance
protection = AssetProtection()
