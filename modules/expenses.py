"""
modules/expenses.py
Expense tracking, persistence, and analysis.
"""

import logging
from datetime import date
from typing import Optional

import pandas as pd

from database.db import execute_query, execute_write
from utils.fx import convert

logger = logging.getLogger(__name__)

EXPENSE_CATEGORIES: list[str] = [
    "Housing",
    "Food & Groceries",
    "Transport",
    "Utilities",
    "Healthcare",
    "Education",
    "Entertainment",
    "Clothing",
    "Money Sent Home",
    "Savings Transfer",
    "Subscriptions",
    "Travel",
    "Personal Care",
    "Gifts & Donations",
    "Other",
]


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def add_expense(
    user_id: int,
    amount: float,
    category: str,
    send_home: float = 0.0,
    expense_date: Optional[str] = None,
    notes: str = "",
) -> dict:
    """Insert a new expense record."""
    if amount <= 0:
        return {"success": False, "error": "Amount must be positive."}
    if not category:
        return {"success": False, "error": "Category is required."}

    expense_date = expense_date or date.today().isoformat()

    try:
        eid = execute_write(
            """
            INSERT INTO expenses (user_id, amount, category, send_home, date, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, amount, category, send_home, expense_date, notes),
        )
        return {"success": True, "expense_id": eid}
    except Exception as exc:
        logger.exception("Failed to add expense: %s", exc)
        return {"success": False, "error": str(exc)}


def get_user_expenses(user_id: int, limit: int = 500) -> pd.DataFrame:
    """Return user expenses as a DataFrame, most recent first."""
    rows = execute_query(
        """
        SELECT * FROM expenses
        WHERE user_id = ?
        ORDER BY date DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    if not rows:
        return pd.DataFrame(
            columns=["id", "user_id", "amount", "category", "send_home", "date", "notes"]
        )
    return pd.DataFrame(rows)


def delete_expense(expense_id: int, user_id: int) -> dict:
    """Delete an expense record scoped to the owning user."""
    try:
        execute_write(
            "DELETE FROM expenses WHERE id = ? AND user_id = ?",
            (expense_id, user_id),
        )
        return {"success": True}
    except Exception as exc:
        logger.exception("Failed to delete expense: %s", exc)
        return {"success": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def expense_analysis(df: pd.DataFrame, income: float, currency: str = "GBP") -> dict:
    """
    Derive spending insights from an expenses DataFrame.

    Returns:
        total_spent, income_pct, category_totals (Series),
        monthly_totals (DataFrame), send_home_total
    """
    if df.empty:
        return {
            "total_spent": 0.0,
            "income_pct": 0.0,
            "category_totals": pd.Series(dtype=float),
            "monthly_totals": pd.DataFrame(),
            "send_home_total": 0.0,
        }

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)

    total_spent = df["amount"].sum()
    income_pct = (total_spent / income * 100) if income else 0.0
    category_totals = (
        df.groupby("category")["amount"].sum().sort_values(ascending=False)
    )
    monthly_totals = (
        df.groupby("month")["amount"].sum().reset_index()
    )
    monthly_totals.columns = ["Month", "Total Spent"]

    send_home_total = df["send_home"].sum()

    return {
        "total_spent": round(total_spent, 2),
        "income_pct": round(income_pct, 1),
        "category_totals": category_totals,
        "monthly_totals": monthly_totals,
        "send_home_total": round(send_home_total, 2),
    }
