"""
ui/stocks_ui.py
Streamlit UI for the Stock Portfolio Tracker.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from modules.stocks import (
    add_stock, remove_stock, get_user_stocks, portfolio_summary,
)
from utils.fx import format_currency


def render_stocks_page(user: dict) -> None:
    st.header("📈 Stock Portfolio")

    # ── Add stock ────────────────────────────────────────────────────────────
    st.subheader("Add / Update Holding")
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        ticker = st.text_input(
            "Ticker Symbol",
            placeholder="AAPL, TSLA, MSFT …",
        ).upper().strip()
    with col2:
        shares = st.number_input(
            "Number of Shares", min_value=0.01, value=1.0, step=0.5, format="%.4f"
        )
    with col3:
        st.write("")
        st.write("")
        add_btn = st.button("➕ Add", use_container_width=True)

    if add_btn:
        if not ticker:
            st.error("Please enter a ticker symbol.")
        else:
            res = add_stock(user["id"], ticker, shares)
            if res["success"]:
                st.success(f"Added {shares} shares of {ticker}.")
                st.rerun()
            else:
                st.error(res["error"])

    st.divider()

    # ── Portfolio summary ────────────────────────────────────────────────────
    with st.spinner("Fetching market data…"):
        summary = portfolio_summary(user["id"])

    if not summary["holdings"]:
        st.info("Your portfolio is empty. Add your first stock above.")
        return

    # Portfolio KPIs
    k1, k2, k3 = st.columns(3)
    k1.metric("Portfolio Value (USD)", f"${summary['total_value']:,.2f}")
    k2.metric(
        "Total P&L",
        f"${summary['total_pnl']:,.2f}",
        delta=f"${summary['total_pnl']:,.2f}",
        delta_color="normal" if summary["total_pnl"] >= 0 else "inverse",
    )
    k3.metric("Holdings", len([h for h in summary["holdings"] if "error" not in h]))

    # Allocation pie
    valid = [h for h in summary["holdings"] if "error" not in h]
    if valid and summary["total_value"] > 0:
        fig_pie = go.Figure(
            go.Pie(
                labels=[h["ticker"] for h in valid],
                values=[h["portfolio_value"] for h in valid],
                hole=0.4,
            )
        )
        fig_pie.update_layout(
            title="Portfolio Allocation",
            height=320,
            margin=dict(t=40, b=10, l=10, r=10),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()
    st.subheader("Individual Holdings")

    for holding in summary["holdings"]:
        ticker = holding["ticker"]
        db_id = holding.get("db_id")

        with st.expander(f"{'❌ ' if 'error' in holding else ''}{ticker}"):
            if "error" in holding:
                st.error(holding["error"])
                col_del = st.columns([5, 1])[1]
                if col_del.button("Remove", key=f"rm_{db_id}"):
                    remove_stock(db_id, user["id"])
                    st.rerun()
                continue

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Shares", f"{holding['shares']:.4f}")
            c2.metric("Current Price", f"${holding['current_price']:,.4f}")
            c3.metric("Portfolio Value", f"${holding['portfolio_value']:,.2f}")
            c4.metric(
                "P&L",
                f"${holding['pnl']:,.2f}",
                delta=f"{holding['pnl_pct']:+.2f}%",
                delta_color="normal" if holding["pnl"] >= 0 else "inverse",
            )

            # Line chart
            history = holding["history"]
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=history.index,
                    y=history["Portfolio Value"],
                    mode="lines",
                    name="Portfolio Value",
                    line=dict(
                        color="#34c97a" if holding["pnl"] >= 0 else "#f74f4f", width=2
                    ),
                    fill="tozeroy",
                    fillcolor=(
                        "rgba(52, 201, 122, 0.15)"
                        if holding["pnl"] >= 0
                        else "rgba(247, 79, 79, 0.15)"
                    ),
                )
            )
            fig.update_layout(
                title=f"{ticker} – 3-Month Performance",
                xaxis_title="Date",
                yaxis_title="Value (USD)",
                height=280,
                margin=dict(t=40, b=10, l=10, r=10),
            )
            st.plotly_chart(fig, use_container_width=True)

            _, del_col = st.columns([5, 1])
            if del_col.button("🗑 Remove", key=f"rm_{db_id}"):
                remove_stock(db_id, user["id"])
                st.rerun()
