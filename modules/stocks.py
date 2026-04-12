"""
modules/stocks.py
Stock portfolio tracker using yfinance.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import yfinance as yf

from database.db import execute_query, execute_write

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def add_stock(user_id: int, ticker: str, shares: float) -> dict:
    """Add or update a stock holding for a user."""
    ticker = ticker.upper().strip()
    if shares <= 0:
        return {"success": False, "error": "Shares must be greater than zero."}
    try:
        existing = execute_query(
            "SELECT id, shares FROM stocks WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        )
        if existing:
            new_shares = existing[0]["shares"] + shares
            execute_write(
                "UPDATE stocks SET shares = ? WHERE id = ?",
                (new_shares, existing[0]["id"]),
            )
        else:
            execute_write(
                "INSERT INTO stocks (user_id, ticker, shares) VALUES (?, ?, ?)",
                (user_id, ticker, shares),
            )
        return {"success": True}
    except Exception as exc:
        logger.exception("Failed to add stock: %s", exc)
        return {"success": False, "error": str(exc)}


def remove_stock(stock_id: int, user_id: int) -> dict:
    """Remove a stock from the portfolio."""
    try:
        execute_write(
            "DELETE FROM stocks WHERE id = ? AND user_id = ?", (stock_id, user_id)
        )
        return {"success": True}
    except Exception as exc:
        logger.exception("Failed to remove stock: %s", exc)
        return {"success": False, "error": str(exc)}


def get_user_stocks(user_id: int) -> list[dict]:
    """Return all stock holdings for a user."""
    return execute_query(
        "SELECT * FROM stocks WHERE user_id = ? ORDER BY ticker", (user_id,)
    )


# ---------------------------------------------------------------------------
# Market data & analytics
# ---------------------------------------------------------------------------

def fetch_history(ticker: str, months: int = 3) -> pd.DataFrame:
    """
    Download up to `months` months of daily OHLCV data.
    Returns empty DataFrame on failure.
    """
    try:
        end = datetime.today()
        start = end - timedelta(days=months * 30)
        df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
        if df.empty:
            logger.warning("No data returned for ticker: %s", ticker)
        return df
    except Exception as exc:
        logger.exception("yfinance error for %s: %s", ticker, exc)
        return pd.DataFrame()


def stock_analysis(ticker: str, shares: float) -> dict:
    """
    Full analysis for a single ticker.

    Returns:
        ticker, shares, history (DataFrame), current_price,
        initial_price, portfolio_value, initial_value, pnl, pnl_pct
    """
    df = fetch_history(ticker)

    if df.empty:
        return {
            "ticker": ticker,
            "shares": shares,
            "error": f"No market data found for '{ticker}'. Please check the ticker symbol.",
        }

    # ── Flatten multi-level columns (yfinance ≥ 0.2.38 returns MultiIndex) ──
    # e.g. ("Close", "AAPL"), ("Open", "AAPL") …
    if isinstance(df.columns, pd.MultiIndex):
        # Keep only the first level that matches "Close"
        close_series = None
        for col in df.columns:
            if col[0] == "Close":
                close_series = df[col]
                break
        if close_series is None:
            return {"ticker": ticker, "shares": shares, "error": "Unexpected data format from yfinance."}
        df = close_series.to_frame(name="Close")
    elif "Close" not in df.columns:
        return {"ticker": ticker, "shares": shares, "error": "Unexpected data format from yfinance."}
    else:
        df = df[["Close"]].copy()

    history = df.copy()
    history["Portfolio Value"] = history["Close"] * shares

    initial_price = float(history["Close"].iloc[0])
    current_price = float(history["Close"].iloc[-1])
    initial_value = initial_price * shares
    portfolio_value = current_price * shares
    pnl = portfolio_value - initial_value
    pnl_pct = (pnl / initial_value * 100) if initial_value else 0.0

    return {
        "ticker": ticker,
        "shares": shares,
        "history": history,
        "current_price": round(current_price, 4),
        "initial_price": round(initial_price, 4),
        "portfolio_value": round(portfolio_value, 2),
        "initial_value": round(initial_value, 2),
        "pnl": round(pnl, 2),
        "pnl_pct": round(pnl_pct, 2),
    }


def portfolio_summary(user_id: int) -> dict:
    """
    Aggregate analysis across all stocks in a user's portfolio.

    Returns total_value, total_pnl, per_ticker results list.
    """
    holdings = get_user_stocks(user_id)
    if not holdings:
        return {"holdings": [], "total_value": 0.0, "total_pnl": 0.0}

    results = []
    total_value = 0.0
    total_pnl = 0.0

    for h in holdings:
        analysis = stock_analysis(h["ticker"], h["shares"])
        analysis["db_id"] = h["id"]
        results.append(analysis)
        if "error" not in analysis:
            total_value += analysis["portfolio_value"]
            total_pnl += analysis["pnl"]

    return {
        "holdings": results,
        "total_value": round(total_value, 2),
        "total_pnl": round(total_pnl, 2),
    }