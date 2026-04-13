"""
ui/dashboard.py
Main dashboard overview – summary cards from all modules.
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import date

from modules.expenses import get_user_expenses, expense_analysis
from modules.savings import get_user_savings, savings_analysis
from modules.stocks import portfolio_summary
from modules.emi import get_user_emis, calculate_emi
from utils.fx import format_currency, convert


def render_dashboard(user: dict) -> None:
    currency = user.get("currency", "GBP")
    income = user.get("income", 0.0)

    st.markdown(
        f"### 👋 Welcome back, **{user['first_name']} {user['last_name']}**"
    )
    st.caption(f"📅 {date.today().strftime('%A, %d %B %Y')}  ·  Currency: {currency}")
    st.divider()

    # ── Fetch data ────────────────────────────────────────────────────────────
    expense_df = get_user_expenses(user["id"], limit=200)
    savings_df = get_user_savings(user["id"])
    exp_analysis = expense_analysis(expense_df, income, currency)
    sav_analysis = savings_analysis(savings_df)

    with st.spinner("Fetching portfolio…"):
        port = portfolio_summary(user["id"])

    emis = get_user_emis(user["id"])
    total_emi = sum(
        calculate_emi(e["loan_amount"], e["interest_rate"], e["tenure"])["emi"]
        for e in emis
    )
    total_emi_gbp = convert(total_emi, emis[0]["currency"] if emis else currency, "GBP") if emis else 0.0

    # ── KPI row ───────────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "💰 Monthly Income",
        format_currency(income, currency),
    )
    k2.metric(
        "💳 Total Spent",
        format_currency(exp_analysis.get("total_spent", 0.0), currency),
        delta=f"{exp_analysis.get('income_pct', 0):.1f}% of income",
        delta_color="inverse" if exp_analysis.get("income_pct", 0) > 80 else "normal",
    )
    k3.metric(
        "📈 Portfolio Value",
        f"${port['total_value']:,.2f}",
        delta=f"P&L ${port['total_pnl']:+,.2f}",
        delta_color="normal" if port["total_pnl"] >= 0 else "inverse",
    )
    k4.metric(
        "🏦 Monthly EMI (GBP)",
        f"£{total_emi_gbp:,.2f}" if emis else "—",
    )

    st.divider()

    # ── Two column layout ─────────────────────────────────────────────────────
    left, right = st.columns(2)

    with left:
        st.subheader("💳 Spending Breakdown")
        if not expense_df.empty:
            cat = exp_analysis.get("category_totals")
            if cat is not None and not cat.empty:
                top5 = cat.head(5)
                fig = go.Figure(
                    go.Bar(
                        x=top5.values,
                        y=top5.index,
                        orientation="h",
                        marker_color="#4f8ef7",
                    )
                )
                fig.update_layout(
                    height=280,
                    margin=dict(t=10, b=10, l=10, r=10),
                    xaxis_title=currency,
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expenses logged yet.")

    with right:
        st.subheader("💰 Savings Progress")
        if not savings_df.empty:
            fig2 = go.Figure()
            fig2.add_trace(
                go.Scatter(
                    x=savings_df["month"],
                    y=savings_df["expected"],
                    name="Expected",
                    line=dict(color="#4f8ef7", dash="dash"),
                )
            )
            fig2.add_trace(
                go.Scatter(
                    x=savings_df["month"],
                    y=savings_df["actual"],
                    name="Actual",
                    line=dict(color="#34c97a"),
                    fill="tozeroy",
                    fillcolor="rgba(52,201,122,0.15)",
                )
            )
            fig2.update_layout(
                height=280,
                margin=dict(t=10, b=10, l=10, r=10),
                yaxis_title=currency,
            )
            st.plotly_chart(fig2, use_container_width=True)
            st.caption(
                f"Savings rate: **{sav_analysis.get('rate', 0):.1f}%** · "
                f"Total saved: **{format_currency(sav_analysis.get('total_actual', 0), currency)}**"
            )
        else:
            st.info("No savings data yet.")

    st.divider()

    # ── Net position ──────────────────────────────────────────────────────────
    st.subheader("📊 Net Financial Position")
    net = income - exp_analysis.get("total_spent", 0.0) - total_emi_gbp

    pos_col1, pos_col2 = st.columns([2, 1])
    with pos_col1:
        categories = ["Income", "Expenses", "EMI Payments", "Net Remaining"]
        values = [
            income,
            -exp_analysis.get("total_spent", 0.0),
            -total_emi_gbp,
            net,
        ]
        colors = ["#34c97a", "#f74f4f", "#f7874f", "#4f8ef7" if net >= 0 else "#f74f4f"]
        fig3 = go.Figure(
            go.Bar(x=categories, y=values, marker_color=colors)
        )
        fig3.update_layout(
            height=280,
            margin=dict(t=10, b=10, l=10, r=10),
            yaxis_title=currency,
        )
        st.plotly_chart(fig3, use_container_width=True)

    with pos_col2:
        st.markdown("#### Quick Stats")
        st.write(f"**Income:** {format_currency(income, currency)}")
        st.write(f"**Expenses:** {format_currency(exp_analysis.get('total_spent', 0), currency)}")
        st.write(f"**EMI (GBP):** £{total_emi_gbp:,.2f}")
        st.write(f"**Net:** {format_currency(net, currency)}")
        st.write(f"**Active Loans:** {len(emis)}")
        st.write(f"**Stocks Held:** {len([h for h in port['holdings'] if 'error' not in h])}")

    # ── Module shortcuts ──────────────────────────────────────────────────────
    st.divider()
    st.subheader("⚡ Quick Actions")
    b1, b2, b3, b4, b5 = st.columns(5)
    if b1.button("➕ Add Expense", use_container_width=True):
        st.session_state["page"] = "Expenses"
        st.rerun()
    if b2.button("💰 Log Savings", use_container_width=True):
        st.session_state["page"] = "Savings"
        st.rerun()
    if b3.button("📈 Add Stock", use_container_width=True):
        st.session_state["page"] = "Stocks"
        st.rerun()
    if b4.button("🏦 Calculate EMI", use_container_width=True):
        st.session_state["page"] = "EMI Calculator"
        st.rerun()
    if b5.button("📰 Read News", use_container_width=True):
        st.session_state["page"] = "News"
        st.rerun()
