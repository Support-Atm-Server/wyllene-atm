"""
Wyllene Enterprise Bank - AI Fraud Detection
Detects suspicious transactions using rule-based and statistical analysis.
"""
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict

class FraudDetector:
    def __init__(self):
        self.thresholds = {
            "large_amount": 50000,        # Flag transactions over $50k
            "velocity_count": 5,          # Max transactions in 10 minutes
            "velocity_window": 10,        # Minutes for velocity check
            "odd_hour_start": 22,         # 10 PM
            "odd_hour_end": 6,            # 6 AM
            "new_account_days": 7,        # Flag new account large transactions
            "max_daily_withdrawal": 100000  # Max daily withdrawal
        }
        self.risk_weights = {
            "large_amount": 30,
            "odd_hour": 20,
            "high_velocity": 35,
            "new_account": 15,
            "daily_limit": 25,
            "unusual_pattern": 20
        }
    
    def analyze_transaction(self, username, amount, txn_type, timestamp=None):
        """
        Analyze a transaction and return a risk score and flags.
        Returns: {"risk_score": 0-100, "flags": [], "block": True/False}
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        flags = []
        risk_score = 0
        
        # ---- CHECK 1: Large amount ----
        if amount > self.thresholds["large_amount"]:
            flags.append(f"⚠️ Large amount: ${amount:,.2f}")
            risk_score += self.risk_weights["large_amount"]
        
        # ---- CHECK 2: Odd hours ----
        hour = timestamp.hour
        if hour >= self.thresholds["odd_hour_start"] or hour < self.thresholds["odd_hour_end"]:
            flags.append(f"🌙 Odd hours: {hour}:00")
            risk_score += self.risk_weights["odd_hour"]
        
        # ---- CHECK 3: High velocity ----
        if self._check_velocity(username, timestamp):
            flags.append("⚡ High transaction velocity")
            risk_score += self.risk_weights["high_velocity"]
        
        # ---- CHECK 4: New account ----
        if self._is_new_account(username):
            flags.append("🆕 New account activity")
            risk_score += self.risk_weights["new_account"]
        
        # ---- CHECK 5: Daily withdrawal limit ----
        if txn_type in ("WITHDRAW", "TRANSFER_OUT"):
            daily_total = self._get_daily_total(username, txn_type, timestamp)
            if daily_total + amount > self.thresholds["max_daily_withdrawal"]:
                flags.append(f"📊 Daily limit approaching: ${daily_total + amount:,.2f}")
                risk_score += self.risk_weights["daily_limit"]
        
        # ---- CHECK 6: Unusual pattern ----
        if self._detect_unusual_pattern(username, amount, txn_type):
            flags.append("🔍 Unusual spending pattern")
            risk_score += self.risk_weights["unusual_pattern"]
        
        # Cap risk score at 100
        risk_score = min(risk_score, 100)
        
        # Block if risk is very high
        block = risk_score >= 70
        
        return {
            "risk_score": risk_score,
            "flags": flags,
            "block": block,
            "status": "🚨 BLOCKED" if block else "⚠️ FLAGGED" if risk_score >= 40 else "✅ SAFE"
        }
    
    def _check_velocity(self, username, timestamp):
        """Check if too many transactions in a short period."""
        conn = sqlite3.connect("atm.db")
        c = conn.cursor()
        window_start = (timestamp - timedelta(minutes=self.thresholds["velocity_window"])).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("SELECT COUNT(*) FROM transactions WHERE username=? AND timestamp > ?",
                  (username, window_start))
        count = c.fetchone()[0]
        conn.close()
        return count >= self.thresholds["velocity_count"]
    
    def _is_new_account(self, username):
        """Check if account was created recently."""
        conn = sqlite3.connect("atm.db")
        c = conn.cursor()
        c.execute("SELECT created_at FROM users WHERE username=?", (username,))
        row = c.fetchone()
        conn.close()
        if row and row[0]:
            created = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
            return (datetime.now() - created).days <= self.thresholds["new_account_days"]
        return False
    
    def _get_daily_total(self, username, txn_type, timestamp):
        """Get total amount for a type of transaction today."""
        conn = sqlite3.connect("atm.db")
        c = conn.cursor()
        today_start = timestamp.strftime("%Y-%m-%d 00:00:00")
        c.execute("SELECT SUM(amount) FROM transactions WHERE username=? AND type=? AND timestamp > ?",
                  (username, txn_type, today_start))
        row = c.fetchone()
        conn.close()
        return row[0] if row[0] else 0.0
    
    def _detect_unusual_pattern(self, username, amount, txn_type):
        """Compare against user's average transaction size."""
        conn = sqlite3.connect("atm.db")
        c = conn.cursor()
        c.execute("SELECT AVG(amount) FROM transactions WHERE username=? AND type=?",
                  (username, txn_type))
        row = c.fetchone()
        conn.close()
        if row[0] and row[0] > 0:
            avg = row[0]
            # Flag if 5x the average
            return amount > avg * 5
        return False
    
    def get_fraud_report(self, days=7):
        """Generate a fraud report for the last N days."""
        conn = sqlite3.connect("atm.db")
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("SELECT * FROM transactions WHERE timestamp > ? ORDER BY amount DESC", (since,))
        rows = c.fetchall()
        conn.close()
        
        report = []
        for row in rows:
            txn = dict(row)
            result = self.analyze_transaction(txn["username"], txn["amount"], txn["type"],
                                              datetime.strptime(txn["timestamp"], "%Y-%m-%d %H:%M:%S"))
            if result["risk_score"] >= 30:
                report.append({**txn, **result})
        
        return report

# Create global instance
detector = FraudDetector()
