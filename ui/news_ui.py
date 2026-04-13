"""
ui/news_ui.py
Streamlit UI for the FinTech News & Sentiment Dashboard.
"""

import streamlit as st

from modules.news import get_stock_news, get_portfolio_news, analyze_sentiment
from modules.stocks import get_user_stocks


def render_news_page(user: dict) -> None:
    st.header("📰 Financial News & Sentiment")

    # ── Tabs: portfolio news vs custom search ─────────────────────────────
    tab1, tab2 = st.tabs(["📊 My Portfolio News", "🔍 Search by Ticker"])

    with tab1:
        _render_portfolio_news(user)

    with tab2:
        _render_ticker_search()


def _render_portfolio_news(user: dict) -> None:
    holdings = get_user_stocks(user["id"])

    if not holdings:
        st.info("Add stocks to your portfolio to see related news here.")
        return

    tickers = [h["ticker"] for h in holdings]
    st.caption(f"Fetching news for: {', '.join(tickers)}")

    with st.spinner("Loading news…"):
        articles = get_portfolio_news(tickers)

    _display_articles(articles)


def _render_ticker_search() -> None:
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker = st.text_input(
            "Enter ticker symbol", placeholder="AAPL, MSFT, GOOGL …"
        ).upper().strip()
    with col2:
        days = st.selectbox("Days back", [1, 3, 7, 14, 30], index=2)

    if st.button("🔍 Fetch News", use_container_width=True):
        if not ticker:
            st.error("Please enter a ticker symbol.")
        else:
            with st.spinner(f"Loading news for {ticker}…"):
                articles = get_stock_news(ticker, days_back=days)
            _display_articles(articles)


def _display_articles(articles: list[dict]) -> None:
    if not articles:
        st.info("No recent articles found.")
        return

    # Sentiment summary bar
    labels = [a["sentiment"]["label"] for a in articles]
    pos = labels.count("Positive")
    neg = labels.count("Negative")
    neu = labels.count("Neutral")

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Total Articles", len(articles))
    s2.metric("📈 Positive", pos)
    s3.metric("📉 Negative", neg)
    s4.metric("😐 Neutral", neu)

    st.divider()

    # Article cards
    for article in articles:
        sentiment = article["sentiment"]
        border_color = (
            "#34c97a" if sentiment["label"] == "Positive"
            else "#f74f4f" if sentiment["label"] == "Negative"
            else "#aaaaaa"
        )

        with st.container():
            col_left, col_right = st.columns([5, 1])
            with col_left:
                st.markdown(
                    f"**[{article['headline']}]({article['url']})**"
                )
                if article["summary"]:
                    st.caption(article["summary"])
                st.caption(
                    f"🗞 {article['source']}  ·  🕐 {article['datetime']}  ·  🏷 {article.get('ticker', '')}"
                )
            with col_right:
                st.markdown(
                    f"<div style='text-align:center; padding:8px; border-radius:8px; "
                    f"background:{border_color}22; border:1px solid {border_color};'>"
                    f"{sentiment['emoji']}<br><small>{sentiment['label']}</small></div>",
                    unsafe_allow_html=True,
                )
            st.divider()
