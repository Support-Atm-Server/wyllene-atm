"""Advanced Analytics Module for Wyllene ATM."""
import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict

class Analytics:
    def __init__(self):
        self.db_file = "atm.db"
    
    def get_transaction_summary(self, days=30):
        """Get transaction summary for the last N days."""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Total volume
        c.execute("SELECT type, SUM(amount), COUNT(*) FROM transactions WHERE timestamp > ? GROUP BY type", (since,))
        by_type = {row[0]: {"total": row[1] or 0, "count": row[2]} for row in c.fetchall()}
        
        # Daily totals
        c.execute("""SELECT DATE(timestamp) as day, SUM(amount), COUNT(*) 
                     FROM transactions WHERE timestamp > ? 
                     GROUP BY day ORDER BY day""", (since,))
        daily = [{"date": row[0], "total": row[1] or 0, "count": row[2]} for row in c.fetchall()]
        
        # Top users
        c.execute("""SELECT username, SUM(amount), COUNT(*) 
                     FROM transactions WHERE timestamp > ? 
                     GROUP BY username ORDER BY SUM(amount) DESC LIMIT 10""", (since,))
        top_users = [{"username": row[0], "total": row[1] or 0, "count": row[2]} for row in c.fetchall()]
        
        conn.close()
        return {"by_type": by_type, "daily": daily, "top_users": top_users}
    
    def get_user_analytics(self, username, days=30):
        """Get detailed analytics for a specific user."""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Spending by type
        c.execute("""SELECT type, SUM(amount), COUNT(*), AVG(amount), MAX(amount)
                     FROM transactions WHERE username=? AND timestamp > ?
                     GROUP BY type""", (username, since))
        by_type = {row[0]: {"total": row[1] or 0, "count": row[2], "avg": row[3] or 0, "max": row[4] or 0} 
                   for row in c.fetchall()}
        
        # Daily spending
        c.execute("""SELECT DATE(timestamp) as day, SUM(amount)
                     FROM transactions WHERE username=? AND timestamp > ?
                     GROUP BY day ORDER BY day""", (username, since))
        daily = [{"date": row[0], "total": row[1] or 0} for row in c.fetchall()]
        
        # Recent transactions
        c.execute("""SELECT * FROM transactions WHERE username=? 
                     ORDER BY id DESC LIMIT 20""", (username,))
        recent = [dict(row) for row in c.fetchall()]
        
        # Total stats
        c.execute("""SELECT COUNT(*), SUM(amount), AVG(amount), MAX(amount), MIN(amount)
                     FROM transactions WHERE username=? AND timestamp > ?""", (username, since))
        row = c.fetchone()
        stats = {"count": row[0], "total": row[1] or 0, "avg": row[2] or 0, "max": row[3] or 0, "min": row[4] or 0}
        
        conn.close()
        return {"by_type": by_type, "daily": daily, "recent": recent, "stats": stats}
    
    def get_department_analytics(self):
        """Get analytics grouped by department."""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("""SELECT u.department, COUNT(t.id) as txn_count, SUM(t.amount) as total_volume
                     FROM transactions t JOIN users u ON t.username = u.username
                     GROUP BY u.department""")
        dept_stats = [dict(row) for row in c.fetchall()]
        
        conn.close()
        return dept_stats
    
    def get_risk_summary(self, days=7):
        """Get fraud risk summary."""
        from fraud_detector import detector
        return detector.get_fraud_report(days)

# Global instance
analytics = Analytics()
