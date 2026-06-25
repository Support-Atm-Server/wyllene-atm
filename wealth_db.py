"""Wyllene Private Wealth — Database operations."""
import sqlite3
import secrets
from datetime import datetime

DB = "wealth.db"

def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init():
    db = connect()
    c = db.cursor()
    
    # Elite clients
    c.execute("""CREATE TABLE IF NOT EXISTS clients (
        username TEXT PRIMARY KEY,
        pin TEXT,
        full_name TEXT,
        tier TEXT DEFAULT 'silver',
        banker_name TEXT,
        invite_code TEXT,
        net_worth REAL DEFAULT 0,
        joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
        chat_id TEXT
    )""")
    
    # Assets
    c.execute("""CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        asset_class TEXT,
        asset_name TEXT,
        value REAL,
        acquired_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    
    # Family links
    c.execute("""CREATE TABLE IF NOT EXISTS family_links (
        head_username TEXT,
        member_username TEXT,
        relationship TEXT,
        linked_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    
    # Concierge requests
    c.execute("""CREATE TABLE IF NOT EXISTS concierge (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        service TEXT,
        details TEXT,
        status TEXT DEFAULT 'pending',
        requested_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    
    db.commit()
    db.close()
    print("✅ Wealth database ready")

def add_client(username, pin, full_name, invite_code):
    """Add a new elite client."""
    import random
    from wealth_config import BANKER_NAMES
    
    db = connect()
    c = db.cursor()
    
    try:
        banker = random.choice(BANKER_NAMES)
        c.execute("""INSERT INTO clients (username, pin, full_name, tier, banker_name, invite_code)
                     VALUES (?,?,?,?,?,?)""",
                  (username, pin, full_name, "silver", banker, invite_code))
        
        # Add initial cash asset
        c.execute("INSERT INTO assets (username, asset_class, asset_name, value) VALUES (?,?,?,?)",
                  (username, "Cash", "USD Wallet", 0))
        
        db.commit()
        return {"status": "ok", "banker": banker}
    except:
        return {"status": "error", "message": "Username exists"}
    finally:
        db.close()

def get_client(username):
    """Get client details."""
    db = connect()
    row = db.execute("SELECT * FROM clients WHERE username=?", (username,)).fetchone()
    db.close()
    return dict(row) if row else None

def get_assets(username):
    """Get all assets for a client."""
    db = connect()
    rows = db.execute("SELECT * FROM assets WHERE username=?", (username,)).fetchall()
    db.close()
    return [dict(row) for row in rows]

def get_net_worth(username):
    """Calculate net worth."""
    db = connect()
    row = db.execute("SELECT SUM(value) FROM assets WHERE username=?", (username,)).fetchone()
    db.close()
    return row[0] if row[0] else 0

def update_tier(username):
    """Update tier based on net worth."""
    from wealth_config import TIERS
    nw = get_net_worth(username)
    
    new_tier = "silver"
    for tier, info in sorted(TIERS.items(), key=lambda x: x[1]["min_balance"], reverse=True):
        if nw >= info["min_balance"]:
            new_tier = tier
            break
    
    db = connect()
    db.execute("UPDATE clients SET tier=?, net_worth=? WHERE username=?", (new_tier, nw, username))
    db.commit()
    db.close()
    return new_tier

def add_asset(username, asset_class, asset_name, value):
    """Add an asset to portfolio."""
    db = connect()
    db.execute("INSERT INTO assets (username, asset_class, asset_name, value) VALUES (?,?,?,?)",
               (username, asset_class, asset_name, value))
    db.commit()
    db.close()
    update_tier(username)

def add_concierge_request(username, service, details):
    """Submit a concierge request."""
    db = connect()
    db.execute("INSERT INTO concierge (username, service, details) VALUES (?,?,?)",
               (username, service, details))
    db.commit()
    db.close()
    return {"status": "ok", "message": f"Your {service} request has been submitted."}
