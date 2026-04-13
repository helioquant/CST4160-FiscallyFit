"""
modules/news.py
Financial news fetcher (Finnhub) with TextBlob sentiment analysis.
Falls back to a demo mode if no API key is configured.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional

import requests
from textblob import TextBlob

logger = logging.getLogger(__name__)

FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")
FINNHUB_BASE = "https://finnhub.io/api/v1"


# ---------------------------------------------------------------------------
# Sentiment
# ---------------------------------------------------------------------------

def analyze_sentiment(text: str) -> dict:
    """
    Score text using TextBlob polarity.

    Returns:
        polarity  – float in [-1, 1]
        label     – "Positive" | "Negative" | "Neutral"
        emoji     – visual indicator
    """
    if not text:
        return {"polarity": 0.0, "label": "Neutral", "emoji": "😐"}

    blob = TextBlob(text)
    polarity: float = blob.sentiment.polarity

    if polarity > 0.1:
        label, emoji = "Positive", "📈"
    elif polarity < -0.1:
        label, emoji = "Negative", "📉"
    else:
        label, emoji = "Neutral", "😐"

    return {"polarity": round(polarity, 3), "label": label, "emoji": emoji}


# ---------------------------------------------------------------------------
# News fetching
# ---------------------------------------------------------------------------

def get_stock_news(ticker: str, days_back: int = 7) -> list[dict]:
    """
    Fetch recent news for a ticker via Finnhub.
    If the API key is missing, returns a list with a demo article.
    """
    ticker = ticker.upper().strip()

    if not FINNHUB_API_KEY:
        logger.warning("FINNHUB_API_KEY not set. Returning demo news.")
        return _demo_news(ticker)

    end_dt = datetime.today()
    start_dt = end_dt - timedelta(days=days_back)
    params = {
        "symbol": ticker,
        "from": start_dt.strftime("%Y-%m-%d"),
        "to": end_dt.strftime("%Y-%m-%d"),
        "token": FINNHUB_API_KEY,
    }

    try:
        resp = requests.get(f"{FINNHUB_BASE}/company-news", params=params, timeout=8)
        resp.raise_for_status()
        raw_articles = resp.json()
    except Exception as exc:
        logger.exception("Finnhub request failed: %s", exc)
        return _demo_news(ticker)

    articles = []
    for item in raw_articles[:20]:  # cap at 20 articles
        headline = item.get("headline", "")
        summary = item.get("summary", "")
        sentiment = analyze_sentiment(f"{headline}. {summary}")

        articles.append(
            {
                "ticker": ticker,
                "headline": headline,
                "summary": summary[:300] + "..." if len(summary) > 300 else summary,
                "source": item.get("source", "Unknown"),
                "url": item.get("url", "#"),
                "datetime": datetime.fromtimestamp(item.get("datetime", 0)).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "sentiment": sentiment,
            }
        )

    return articles if articles else _demo_news(ticker)


def get_portfolio_news(tickers: list[str]) -> list[dict]:
    """Aggregate news for all tickers in a portfolio."""
    all_articles: list[dict] = []
    seen_urls: set[str] = set()

    for ticker in tickers:
        for article in get_stock_news(ticker, days_back=3):
            url = article.get("url", "")
            if url not in seen_urls:
                all_articles.append(article)
                seen_urls.add(url)

    # Sort by datetime descending
    all_articles.sort(key=lambda x: x.get("datetime", ""), reverse=True)
    return all_articles[:30]


# ---------------------------------------------------------------------------
# Demo fallback
# ---------------------------------------------------------------------------

def _demo_news(ticker: str) -> list[dict]:
    """Return sample articles when the API key is not configured."""
    sample = [
        {
            "ticker": ticker,
            "headline": f"[DEMO] {ticker} reports strong quarterly earnings",
            "summary": (
                f"This is a demo article. Add your FINNHUB_API_KEY to .env "
                f"to see real news for {ticker}."
            ),
            "source": "FiscallyFit Demo",
            "url": "#",
            "datetime": datetime.today().strftime("%Y-%m-%d %H:%M"),
            "sentiment": {"polarity": 0.3, "label": "Positive", "emoji": "📈"},
        },
        {
            "ticker": ticker,
            "headline": f"[DEMO] Analysts remain cautious on {ticker} outlook",
            "summary": "Add a Finnhub API key to retrieve live financial news.",
            "source": "FiscallyFit Demo",
            "url": "#",
            "datetime": datetime.today().strftime("%Y-%m-%d %H:%M"),
            "sentiment": {"polarity": -0.1, "label": "Neutral", "emoji": "😐"},
        },
    ]
    return sample
