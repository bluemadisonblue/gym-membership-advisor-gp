"""
Admin authentication and authorization utilities.

This module provides simple password-based authentication for admin access.
For production, consider using more robust authentication (OAuth, 2FA, etc.)
"""

import os
import hashlib
import secrets
from functools import wraps
from flask import session, redirect, url_for, flash


# Admin credentials (set via environment variables)
# Default password: "admin123" (change this in production!)
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.environ.get(
    "ADMIN_PASSWORD_HASH",
    "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"  # admin123
)


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(password) == password_hash


def is_admin_logged_in() -> bool:
    """Check if the current user is logged in as admin."""
    return session.get("is_admin", False) and session.get("admin_username") == ADMIN_USERNAME


def require_admin(f):
    """Decorator to require admin authentication for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin_logged_in():
            flash("Admin access required. Please log in.", "error")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function


def generate_csrf_token() -> str:
    """Generate a CSRF token for forms."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def verify_csrf_token(token: str) -> bool:
    """Verify a CSRF token."""
    return token == session.get("csrf_token")


def generate_admin_password_hash(password: str):
    """
    Helper function to generate password hash.
    Run this to get the hash for your admin password:
    
    python3 -c "from admin_auth import generate_admin_password_hash; generate_admin_password_hash('your_password')"
    """
    password_hash = hash_password(password)
    print(f"\nPassword Hash for '{password}':")
    print(password_hash)
    print("\nSet this as ADMIN_PASSWORD_HASH environment variable:")
    print(f"export ADMIN_PASSWORD_HASH='{password_hash}'")
    return password_hash


# Security logging
def log_admin_action(action: str, details: str = ""):
    """Log admin actions for security auditing."""
    from datetime import datetime
    timestamp = datetime.utcnow().isoformat()
    username = session.get("admin_username", "unknown")
    ip_address = session.get("admin_ip", "unknown")
    
    log_entry = f"[{timestamp}] ADMIN: {username} ({ip_address}) - {action}"
    if details:
        log_entry += f" - {details}"
    
    # In production, write to a secure log file or logging service
    print(log_entry)
    
    # TODO: Consider adding database logging for audit trail
    # AdminLog.create(
    #     username=username,
    #     action=action,
    #     details=details,
    #     ip_address=ip_address,
    #     timestamp=timestamp
    # )
