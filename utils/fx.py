"""
utils/fx.py
Currency conversion using the Frankfurter open API (no key required).
Falls back to a static table of approximate rates if the API is unavailable.
"""

import logging
import os
import requests
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

# Static fallback rates (approximate, relative to GBP)
_FALLBACK_RATES_TO_GBP: dict[str, float] = {
    "GBP": 1.0,
    "USD": 0.79,
    "EUR": 0.86,
    "INR": 0.0095,
    "AUD": 0.51,
    "CAD": 0.58,
    "JPY": 0.0053,
    "CNY": 0.11,
    "AED": 0.22,
    "SGD": 0.59,
    "PKR": 0.0028,
    "NGN": 0.00052,
    "GHS": 0.054,
    "ZAR": 0.042,
    "BRL": 0.16,
    "MXN": 0.046,
    "CHF": 0.89,
    "SEK": 0.075,
    "NOK": 0.074,
    "DKK": 0.115,
    "PLN": 0.20,
    "HKD": 0.101,
    "NZD": 0.48,
    "TRY": 0.024,
    "KES": 0.0062,
    "EGP": 0.016,
    "MYR": 0.17,
    "THB": 0.022,
    "PHP": 0.014,
    "IDR": 0.000050,
    "VND": 0.000032,
    "BDT": 0.0072,
    "LKR": 0.0027,
    "NPR": 0.006,
}

SUPPORTED_CURRENCIES: list[str] = sorted(_FALLBACK_RATES_TO_GBP.keys())

FRANKFURTER_BASE = "https://api.frankfurter.app"


def get_rate(from_currency: str, to_currency: str = "GBP") -> float:
    """
    Return conversion rate: 1 unit of from_currency → to_currency.
    Tries Frankfurter API first, falls back to static table.
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    if from_currency == to_currency:
        return 1.0

    try:
        url = f"{FRANKFURTER_BASE}/latest?from={from_currency}&to={to_currency}"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        rate = data["rates"].get(to_currency)
        if rate:
            return float(rate)
    except Exception as exc:
        logger.warning("FX API unavailable (%s). Using fallback rates.", exc)

    # Static fallback: convert via GBP as pivot
    from_to_gbp = _FALLBACK_RATES_TO_GBP.get(from_currency)
    to_to_gbp = _FALLBACK_RATES_TO_GBP.get(to_currency)

    if from_to_gbp and to_to_gbp:
        return from_to_gbp / to_to_gbp

    logger.error("No rate available for %s → %s", from_currency, to_currency)
    return 1.0  # safe default


def convert(amount: float, from_currency: str, to_currency: str = "GBP") -> float:
    """Convert amount from one currency to another."""
    if amount == 0:
        return 0.0
    rate = get_rate(from_currency, to_currency)
    return round(amount * rate, 2)


def format_currency(amount: float, currency: str = "GBP") -> str:
    """Format a monetary value with the appropriate symbol."""
    symbols = {
        "GBP": "£", "USD": "$", "EUR": "€", "INR": "₹",
        "JPY": "¥", "CNY": "¥", "AUD": "A$", "CAD": "C$",
        "CHF": "Fr", "AED": "د.إ", "SGD": "S$",
    }
    sym = symbols.get(currency.upper(), currency.upper() + " ")
    return f"{sym}{amount:,.2f}"
