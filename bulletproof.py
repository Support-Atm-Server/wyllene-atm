"""Wyllene Dynasty — Bulletproofing Layer."""
import functools
import time
import sqlite3
import os
import shutil
from datetime import datetime
from flask import request, jsonify, make_response

# ---------- RATE LIMITING ----------
rate_limits = {}

def rate_limit(max_requests=30, window=60):
    """Limit requests per IP."""
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            ip = request.remote_addr or 'unknown'
            now = time.time()
            
            if ip not in rate_limits:
                rate_limits[ip] = []
            
            # Clean old entries
            rate_limits[ip] = [t for t in rate_limits[ip] if now - t < window]
            
            if len(rate_limits[ip]) >= max_requests:
                return "⚠️ Rate limit exceeded. Please wait.", 429
            
            rate_limits[ip].append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator

# ---------- ERROR HANDLER ----------
def safe_route(f):
    """Wrap route with error handling."""
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            log_error(f.__name__, error_msg)
            return f"""
            <!DOCTYPE html><html><head><title>Error</title>
            <style>body{{font-family:Georgia;background:#050510;color:#e0e0e0;padding:50px;text-align:center}}
            h1{{color:#FF4444}}p{{color:#aaa}}a{{color:#D4AF37}}</style></head><body>
            <h1>⚠️ System Error</h1><p>Something went wrong. Our team has been notified.</p>
            <p style='color:#888;font-size:12px'>Ref: {datetime.now().strftime('%Y%m%d%H%M%S')}</p>
            <a href='/dashboard'>Return to Command Center</a></body></html>""", 500
    return wrapped

# ---------- LOGGING ----------
def log_error(route, error):
    """Log errors to file."""
    os.makedirs('logs', exist_ok=True)
    with open('logs/errors.log', 'a') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {route}: {error}\n")

def log_access(route, ip):
    """Log access to file."""
    os.makedirs('logs', exist_ok=True)
    with open('logs/access.log', 'a') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {ip} -> {route}\n")

# ---------- SECURITY HEADERS ----------
def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000'
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net"
    return response

# ---------- INPUT SANITIZATION ----------
def sanitize_input(text):
    """Sanitize user input."""
    if not text:
        return ""
    # Remove potentially dangerous characters
    import re
    text = re.sub(r'[<>{}]', '', str(text))
    text = text.strip()[:500]  # Max 500 chars
    return text

# ---------- DATABASE BACKUP ----------
def backup_database():
    """Create a timestamped backup of the database."""
    os.makedirs('backups', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for db_file in ['atm.db', 'dynasty.db', 'wealth.db']:
        if os.path.exists(db_file):
            backup_name = f'backups/{db_file}_{timestamp}.bak'
            shutil.copy2(db_file, backup_name)
    
    # Keep only last 7 backups
    backups = sorted(os.listdir('backups'))
    while len(backups) > 21:  # 7 days × 3 databases
        os.remove(f'backups/{backups[0]}')
        backups.pop(0)
    
    return f"Backup completed at {timestamp}"

# ---------- HEALTH CHECK ----------
def system_health():
    """Check all systems are operational."""
    checks = {
        "server": True,
        "database": False,
        "disk_space": False,
        "timestamp": datetime.now().isoformat()
    }
    
    # Check database
    try:
        conn = sqlite3.connect("dynasty.db")
        conn.execute("SELECT 1")
        conn.close()
        checks["database"] = True
    except:
        pass
    
    # Check disk space
    try:
        stat = os.statvfs('.')
        free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
        checks["disk_space"] = free_gb > 1  # More than 1GB free
        checks["disk_free_gb"] = round(free_gb, 2)
    except:
        pass
    
    return checks

# ---------- PERFORMANCE CACHE ----------
cache = {}
def cached(ttl=60):
    """Cache function results for TTL seconds."""
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            key = f"{f.__name__}:{args}:{kwargs}"
            now = time.time()
            
            if key in cache and now - cache[key]['time'] < ttl:
                return cache[key]['data']
            
            result = f(*args, **kwargs)
            cache[key] = {'time': now, 'data': result}
            return result
        return wrapped
    return decorator

print("✅ Bulletproof module loaded")
