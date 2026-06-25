"""Wyllene Dynasty — Military-Grade Security Fortress."""
import hashlib
import secrets
import time
import re
from datetime import datetime, timedelta

class SecurityFortress:
    def __init__(self):
        self.failed_attempts = {}
        self.locked_accounts = {}
        self.session_tokens = {}
        self.two_factor_codes = {}
        
        # Security policies
        self.policies = {
            "min_pin_length": 6,
            "max_login_attempts": 3,
            "lockout_duration_minutes": 30,
            "session_timeout_minutes": 60,
            "two_factor_timeout_seconds": 300,
            "password_history_count": 5,
            "inactivity_lockout_days": 90,
            "require_special_chars": True,
            "require_numbers": True,
            "ip_whitelist_enabled": False,
        }
    
    # ---------- PIN HASHING (SHA-256 + Salt) ----------
    def hash_pin(self, pin, salt=None):
        """Hash a PIN with salt using SHA-256."""
        if not salt:
            salt = secrets.token_hex(16)
        hashed = hashlib.sha256(f"{pin}{salt}".encode()).hexdigest()
        return {"hash": hashed, "salt": salt}
    
    def verify_pin(self, pin, stored_hash, salt):
        """Verify a PIN against stored hash."""
        computed = hashlib.sha256(f"{pin}{salt}".encode()).hexdigest()
        return computed == stored_hash
    
    # ---------- RATE LIMITING & LOCKOUT ----------
    def check_login_attempt(self, username, ip_address):
        """Check if login is allowed. Returns True if allowed, False if locked."""
        key = f"{username}:{ip_address}"
        
        # Check if account is locked
        if username in self.locked_accounts:
            lock_time = self.locked_accounts[username]
            if datetime.now() < lock_time:
                remaining = (lock_time - datetime.now()).seconds // 60
                return {"allowed": False, "reason": f"Account locked. Try again in {remaining} minutes."}
            else:
                del self.locked_accounts[username]
                self.failed_attempts[key] = 0
        
        # Check failed attempts
        attempts = self.failed_attempts.get(key, 0)
        if attempts >= self.policies["max_login_attempts"]:
            self.locked_accounts[username] = datetime.now() + timedelta(minutes=self.policies["lockout_duration_minutes"])
            return {"allowed": False, "reason": f"Too many attempts. Locked for {self.policies['lockout_duration_minutes']} minutes."}
        
        return {"allowed": True}
    
    def record_failed_attempt(self, username, ip_address):
        """Record a failed login attempt."""
        key = f"{username}:{ip_address}"
        self.failed_attempts[key] = self.failed_attempts.get(key, 0) + 1
    
    def reset_attempts(self, username, ip_address):
        """Reset failed attempts after successful login."""
        key = f"{username}:{ip_address}"
        if key in self.failed_attempts:
            del self.failed_attempts[key]
    
    # ---------- SESSION MANAGEMENT ----------
    def create_session(self, username):
        """Create a secure session token."""
        token = secrets.token_hex(32)
        self.session_tokens[token] = {
            "username": username,
            "created": datetime.now(),
            "expires": datetime.now() + timedelta(minutes=self.policies["session_timeout_minutes"]),
            "ip": "tracked"
        }
        return token
    
    def validate_session(self, token):
        """Validate a session token."""
        if token not in self.session_tokens:
            return False
        session = self.session_tokens[token]
        if datetime.now() > session["expires"]:
            del self.session_tokens[token]
            return False
        return session["username"]
    
    def destroy_session(self, token):
        """Destroy a session (logout)."""
        if token in self.session_tokens:
            del self.session_tokens[token]
    
    # ---------- TWO-FACTOR AUTHENTICATION ----------
    def generate_2fa_code(self, username):
        """Generate a 2FA code."""
        code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        self.two_factor_codes[username] = {
            "code": code,
            "expires": time.time() + self.policies["two_factor_timeout_seconds"]
        }
        return code
    
    def verify_2fa_code(self, username, code):
        """Verify a 2FA code."""
        if username not in self.two_factor_codes:
            return False
        stored = self.two_factor_codes[username]
        if time.time() > stored["expires"]:
            del self.two_factor_codes[username]
            return False
        if stored["code"] != code:
            return False
        del self.two_factor_codes[username]
        return True
    
    # ---------- INPUT VALIDATION ----------
    def validate_username(self, username):
        """Validate username format."""
        if not username or len(username) < 3 or len(username) > 30:
            return False
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False
        return True
    
    def validate_pin(self, pin):
        """Validate PIN strength."""
        if not pin or len(pin) < self.policies["min_pin_length"]:
            return False, f"PIN must be at least {self.policies['min_pin_length']} characters"
        if self.policies["require_numbers"] and not re.search(r'\d', pin):
            return False, "PIN must contain at least one number"
        if self.policies["require_special_chars"] and not re.search(r'[!@#$%^&*]', pin):
            return False, "PIN must contain at least one special character"
        return True, "PIN is strong"
    
    def validate_email(self, email):
        """Validate email format."""
        if not email:
            return True  # Email is optional
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def sanitize_input(self, text):
        """Sanitize user input to prevent injection."""
        if not text:
            return ""
        # Remove HTML tags
        text = re.sub(r'<[^>]*>', '', text)
        # Remove script attempts
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        # Remove SQL injection patterns
        text = re.sub(r'(\bSELECT\b|\bINSERT\b|\bDELETE\b|\bDROP\b|\bUNION\b)', '', text, flags=re.IGNORECASE)
        # Limit length
        return text.strip()[:200]
    
    # ---------- AUDIT LOGGING ----------
    def log_security_event(self, event_type, username, ip_address, details=""):
        """Log a security event."""
        import os
        os.makedirs('logs', exist_ok=True)
        with open('logs/security.log', 'a') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] {event_type} | User: {username} | IP: {ip_address} | {details}\n")
    
    # ---------- SECURITY REPORT ----------
    def get_security_report(self):
        """Generate a security status report."""
        return {
            "failed_attempts_tracked": len(self.failed_attempts),
            "locked_accounts": len(self.locked_accounts),
            "active_sessions": len(self.session_tokens),
            "policies": self.policies,
            "timestamp": datetime.now().isoformat(),
        }

# Global instance
security = SecurityFortress()
