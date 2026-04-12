"""
ui/expenses_ui.py
Streamlit UI for the Expense Tracker.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import date

from modules.expenses import (
    add_expense, get_user_expenses, delete_expense,
    expense_analysis, EXPENSE_CATEGORIES,
)
from utils.fx import format_currency, convert, SUPPORTED_CURRENCIES


def render_expenses_page(user: dict) -> None:
    st.header("💳 Expense Tracker")
    currency = user.get("currency", "GBP")
    income = user.get("income", 0.0)

    # ── Add expense ───────────────────────────────────────────────────────────
    st.subheader("Log New Expense")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        amount = st.number_input(
            f"Amount ({currency})", min_value=0.01, value=50.0, step=5.0, format="%.2f"
        )
    with col2:
        category = st.selectbox("Category", EXPENSE_CATEGORIES)
    with col3:
        send_home = st.number_input(
            "Money Sent Home", min_value=0.0, value=0.0, step=10.0, format="%.2f",
            help="Amount sent to family/abroad in your local currency"
        )
    with col4:
        expense_date = st.date_input("Date", value=date.today())

    notes = st.text_input("Notes (optional)", placeholder="e.g. Weekly groceries")

    if st.button("➕ Add Expense", use_container_width=True):
        res = add_expense(
            user["id"],
            amount,
            category,
            send_home,
            expense_date.isoformat(),
            notes,
        )
        if res["success"]:
            st.success("Expense recorded!")
            st.rerun()
        else:
            st.error(res["error"])

    st.divider()

    # ── Analytics ─────────────────────────────────────────────────────────────
    df = get_user_expenses(user["id"])

    if df.empty:
        st.info("No expenses yet. Log your first one above.")
        return

    analysis = expense_analysis(df, income, currency)

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Spent", format_currency(analysis["total_spent"], currency))
    k2.metric(
        "% of Income",
        f"{analysis['income_pct']:.1f}%",
        delta="over budget" if analysis["income_pct"] > 80 else "within budget",
        delta_color="inverse" if analysis["income_pct"] > 80 else "normal",
    )
    k3.metric("Money Sent Home", format_currency(analysis["send_home_total"], currency))
    k4.metric("Transactions", len(df))

    # Budget health bar
    budget_pct = min(analysis["income_pct"] / 100, 1.0) if income else 0.0
    bar_color = "🟢" if budget_pct < 0.6 else "🟡" if budget_pct < 0.85 else "🔴"
    st.markdown(f"{bar_color} **Budget Usage**")
    st.progress(budget_pct)

    # Charts
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        cat = analysis["category_totals"]
        if not cat.empty:
            fig_pie = go.Figure(
                go.Pie(
                    labels=cat.index.tolist(),
                    values=cat.values.tolist(),
                    hole=0.4,
                )
            )
            fig_pie.update_layout(
                title="Spending by Category",
                height=350,
                margin=dict(t=40, b=10, l=10, r=10),
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    with chart_col2:
        monthly = analysis["monthly_totals"]
        if not monthly.empty:
            fig_bar = go.Figure(
                go.Bar(
                    x=monthly["Month"],
                    y=monthly["Total Spent"],
                    marker_color="#4f8ef7",
                )
            )
            if income:
                fig_bar.add_hline(
                    y=income,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Income",
                )
            fig_bar.update_layout(
                title="Monthly Spending",
                xaxis_title="Month",
                yaxis_title=f"Spent ({currency})",
                height=350,
                margin=dict(t=40, b=10, l=10, r=10),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    # Transactions table
    st.subheader("📋 Recent Transactions")
    display_df = df.head(50).copy()

    for _, row in display_df.iterrows():
        c1, c2, c3, c4, c5, c6 = st.columns([2, 3, 2, 2, 2, 1])
        c1.caption(str(row["date"]))
        c2.write(row["category"])
        c3.write(format_currency(row["amount"], currency))
        if row["send_home"] > 0:
            c4.write(f"🏡 {format_currency(row['send_home'], currency)}")
        else:
            c4.write("—")
        c5.caption(str(row["notes"]) if row["notes"] else "")
        if c6.button("🗑", key=f"del_exp_{row['id']}"):
            delete_expense(int(row["id"]), user["id"])
            st.rerun()
