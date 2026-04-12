"""
modules/savings.py
Savings tracking and analysis.
"""

import logging
import pandas as pd
from typing import Optional

from database.db import execute_query, execute_write

logger = logging.getLogger(__name__)


def save_savings(
    user_id: int, expected: float, actual: float, month: str
) -> dict:
    """
    Upsert a savings record for a given month.
    If a record for that month already exists it is updated.
    """
    try:
        existing = execute_query(
            "SELECT id FROM savings WHERE user_id = ? AND month = ?",
            (user_id, month),
        )
        if existing:
            execute_write(
                "UPDATE savings SET expected = ?, actual = ? WHERE id = ?",
                (expected, actual, existing[0]["id"]),
            )
        else:
            execute_write(
                "INSERT INTO savings (user_id, expected, actual, month) VALUES (?, ?, ?, ?)",
                (user_id, expected, actual, month),
            )
        return {"success": True}
    except Exception as exc:
        logger.exception("Failed to save savings: %s", exc)
        return {"success": False, "error": str(exc)}


def get_user_savings(user_id: int) -> pd.DataFrame:
    """Return all savings rows for a user as a sorted DataFrame."""
    rows = execute_query(
        "SELECT * FROM savings WHERE user_id = ? ORDER BY month ASC", (user_id,)
    )
    if not rows:
        return pd.DataFrame(columns=["id", "user_id", "expected", "actual", "month"])
    return pd.DataFrame(rows)


def savings_analysis(df: pd.DataFrame) -> dict:
    """
    Compute savings insights from a DataFrame with columns [expected, actual, month].

    Returns:
        remaining       – how much is still unaccounted for (expected - actual, latest)
        avg_expected    – historical average expected
        avg_actual      – historical average actual
        total_expected  – cumulative expected
        total_actual    – cumulative actual
        total_surplus   – positive means ahead of plan; negative means behind
        rate            – actual/expected × 100 (%)
    """
    if df.empty:
        return {}

    df = df.copy()
    df["surplus"] = df["actual"] - df["expected"]

    latest = df.iloc[-1]
    remaining = max(latest["expected"] - latest["actual"], 0.0)

    return {
        "remaining": round(remaining, 2),
        "avg_expected": round(df["expected"].mean(), 2),
        "avg_actual": round(df["actual"].mean(), 2),
        "total_expected": round(df["expected"].sum(), 2),
        "total_actual": round(df["actual"].sum(), 2),
        "total_surplus": round(df["surplus"].sum(), 2),
        "rate": round((df["actual"].sum() / df["expected"].sum()) * 100, 1)
        if df["expected"].sum() > 0
        else 0.0,
    }


def delete_savings(savings_id: int, user_id: int) -> dict:
    """Delete a savings record."""
    try:
        execute_write(
            "DELETE FROM savings WHERE id = ? AND user_id = ?",
            (savings_id, user_id),
        )
        return {"success": True}
    except Exception as exc:
        logger.exception("Failed to delete savings: %s", exc)
        return {"success": False, "error": str(exc)}
