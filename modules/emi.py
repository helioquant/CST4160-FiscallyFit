"""
modules/emi.py
EMI (Equated Monthly Instalment) business logic.
Uses the reducing-balance compound-interest formula.
"""

import math
import logging
import pandas as pd
from typing import Optional

from database.db import execute_query, execute_write
from utils.fx import convert, format_currency

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core calculation
# ---------------------------------------------------------------------------

def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> dict:
    """
    Calculate EMI using the reducing balance formula:
        EMI = P * r * (1+r)^n / ((1+r)^n - 1)

    Args:
        principal:      Loan amount
        annual_rate:    Annual interest rate in % (e.g. 8.5 for 8.5%)
        tenure_months:  Loan duration in months

    Returns a dict with:
        emi, total_payable, total_interest, schedule (DataFrame)
    """
    if principal <= 0 or tenure_months <= 0:
        raise ValueError("Principal and tenure must be positive.")

    if annual_rate == 0:
        emi = principal / tenure_months
        total_payable = principal
        total_interest = 0.0
    else:
        r = (annual_rate / 100) / 12          # monthly rate
        n = tenure_months
        emi = principal * r * math.pow(1 + r, n) / (math.pow(1 + r, n) - 1)
        total_payable = emi * n
        total_interest = total_payable - principal

    # Build amortisation schedule
    schedule_rows = []
    balance = principal
    r_monthly = (annual_rate / 100) / 12

    for month in range(1, tenure_months + 1):
        interest_component = balance * r_monthly if annual_rate > 0 else 0.0
        principal_component = emi - interest_component
        balance -= principal_component
        if balance < 0:
            balance = 0.0
        schedule_rows.append(
            {
                "Month": month,
                "EMI": round(emi, 2),
                "Principal": round(principal_component, 2),
                "Interest": round(interest_component, 2),
                "Balance": round(balance, 2),
            }
        )

    schedule = pd.DataFrame(schedule_rows)

    return {
        "emi": round(emi, 2),
        "total_payable": round(total_payable, 2),
        "total_interest": round(total_interest, 2),
        "schedule": schedule,
    }


def emi_in_gbp(emi_amount: float, source_currency: str) -> float:
    """Convert an EMI value to GBP using live FX rates."""
    return convert(emi_amount, source_currency, "GBP")


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def save_emi(
    user_id: int,
    label: str,
    loan_amount: float,
    interest_rate: float,
    tenure: int,
    currency: str,
) -> dict:
    """Persist an EMI record for a user."""
    try:
        emi_id = execute_write(
            """
            INSERT INTO emi (user_id, label, loan_amount, interest_rate, tenure, currency)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, label, loan_amount, interest_rate, tenure, currency.upper()),
        )
        return {"success": True, "emi_id": emi_id}
    except Exception as exc:
        logger.exception("Failed to save EMI: %s", exc)
        return {"success": False, "error": str(exc)}


def get_user_emis(user_id: int) -> list[dict]:
    """Retrieve all EMI records for a user."""
    return execute_query(
        "SELECT * FROM emi WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    )


def delete_emi(emi_id: int, user_id: int) -> dict:
    """Delete an EMI record (scoped to the owning user)."""
    try:
        execute_write(
            "DELETE FROM emi WHERE id = ? AND user_id = ?", (emi_id, user_id)
        )
        return {"success": True}
    except Exception as exc:
        logger.exception("Failed to delete EMI: %s", exc)
        return {"success": False, "error": str(exc)}
