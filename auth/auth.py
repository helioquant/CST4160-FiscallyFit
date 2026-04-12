"""
auth/auth.py
Authentication service: registration, login, profile updates.
Passwords are hashed with bcrypt before storage.
"""

import bcrypt
import logging
from typing import Optional

from database.db import execute_query, execute_write

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash_password(plain: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain.encode(), salt).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def register_user(
    first_name: str,
    last_name: str,
    username: str,
    password: str,
    income: float = 0.0,
    currency: str = "GBP",
) -> dict:
    """
    Register a new user.

    Returns:
        {"success": True, "user_id": int} on success
        {"success": False, "error": str}  on failure
    """
    # Validate inputs
    if not all([first_name.strip(), last_name.strip(), username.strip(), password]):
        return {"success": False, "error": "All fields are required."}

    if len(password) < 8:
        return {"success": False, "error": "Password must be at least 8 characters."}

    # Check username uniqueness
    existing = execute_query(
        "SELECT id FROM users WHERE username = ?", (username.strip().lower(),)
    )
    if existing:
        return {"success": False, "error": "Username already taken. Please choose another."}

    hashed = _hash_password(password)
    try:
        user_id = execute_write(
            """
            INSERT INTO users (first_name, last_name, username, password, income, currency)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                first_name.strip(),
                last_name.strip(),
                username.strip().lower(),
                hashed,
                income,
                currency.upper(),
            ),
        )
        logger.info("User registered: %s (id=%s)", username, user_id)
        return {"success": True, "user_id": user_id}
    except Exception as exc:
        logger.exception("Registration failed: %s", exc)
        return {"success": False, "error": "Registration failed. Please try again."}


def login_user(username: str, password: str) -> dict:
    """
    Authenticate a user.

    Returns:
        {"success": True, "user": dict} on success
        {"success": False, "error": str} on failure
    """
    if not username or not password:
        return {"success": False, "error": "Username and password are required."}

    rows = execute_query(
        "SELECT * FROM users WHERE username = ?", (username.strip().lower(),)
    )
    if not rows:
        return {"success": False, "error": "Invalid username or password."}

    user = rows[0]
    if not _verify_password(password, user["password"]):
        return {"success": False, "error": "Invalid username or password."}

    # Return user dict without password
    safe_user = {k: v for k, v in user.items() if k != "password"}
    logger.info("User logged in: %s", username)
    return {"success": True, "user": safe_user}


def get_user(user_id: int) -> Optional[dict]:
    """Fetch a user record by id (without password)."""
    rows = execute_query("SELECT * FROM users WHERE id = ?", (user_id,))
    if not rows:
        return None
    return {k: v for k, v in rows[0].items() if k != "password"}


def update_user(
    user_id: int,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    income: Optional[float] = None,
    currency: Optional[str] = None,
    new_password: Optional[str] = None,
) -> dict:
    """
    Update allowed user fields.

    Returns:
        {"success": True} or {"success": False, "error": str}
    """
    updates = []
    params = []

    if first_name is not None:
        updates.append("first_name = ?")
        params.append(first_name.strip())
    if last_name is not None:
        updates.append("last_name = ?")
        params.append(last_name.strip())
    if income is not None:
        if income < 0:
            return {"success": False, "error": "Income cannot be negative."}
        updates.append("income = ?")
        params.append(income)
    if currency is not None:
        updates.append("currency = ?")
        params.append(currency.upper())
    if new_password is not None:
        if len(new_password) < 8:
            return {"success": False, "error": "Password must be at least 8 characters."}
        updates.append("password = ?")
        params.append(_hash_password(new_password))

    if not updates:
        return {"success": False, "error": "No fields to update."}

    params.append(user_id)
    sql = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"

    try:
        execute_write(sql, tuple(params))
        return {"success": True}
    except Exception as exc:
        logger.exception("Update user failed: %s", exc)
        return {"success": False, "error": "Update failed. Please try again."}
