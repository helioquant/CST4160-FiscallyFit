"""
ui/savings_ui.py
Streamlit UI for the Savings module.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import date

from modules.savings import save_savings, get_user_savings, savings_analysis, delete_savings
from utils.fx import format_currency


def render_savings_page(user: dict) -> None:
    st.header("💰 Savings Tracker")
    currency = user.get("currency", "GBP")

    # ── Add / update savings ─────────────────────────────────────────────────
    st.subheader("Log Monthly Savings")
    col1, col2, col3 = st.columns(3)

    with col1:
        month = st.text_input(
            "Month (YYYY-MM)",
            value=date.today().strftime("%Y-%m"),
            help="Format: 2024-03",
        )
    with col2:
        expected = st.number_input(
            f"Expected Savings ({currency})",
            min_value=0.0,
            value=500.0,
            step=50.0,
            format="%.2f",
        )
    with col3:
        actual = st.number_input(
            f"Actual Savings ({currency})",
            min_value=0.0,
            value=400.0,
            step=50.0,
            format="%.2f",
        )

    if st.button("💾 Save Record", use_container_width=True):
        if not month or len(month) != 7:
            st.error("Please enter a valid month in YYYY-MM format.")
        else:
            res = save_savings(user["id"], expected, actual, month)
            if res["success"]:
                st.success(f"Savings for {month} saved!")
                st.rerun()
            else:
                st.error(res["error"])

    st.divider()

    # ── History & analytics ──────────────────────────────────────────────────
    df = get_user_savings(user["id"])

    if df.empty:
        st.info("No savings data yet. Log your first month above.")
        return

    analysis = savings_analysis(df)

    # KPI cards
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Total Actual Saved",
        format_currency(analysis["total_actual"], currency),
        delta=f"{analysis['rate']}% of target",
    )
    k2.metric(
        "Total Expected",
        format_currency(analysis["total_expected"], currency),
    )
    k3.metric(
        "Surplus / Deficit",
        format_currency(abs(analysis["total_surplus"]), currency),
        delta="ahead" if analysis["total_surplus"] >= 0 else "behind",
        delta_color="normal" if analysis["total_surplus"] >= 0 else "inverse",
    )
    k4.metric(
        "Avg Monthly Saved",
        format_currency(analysis["avg_actual"], currency),
    )

    # Progress bar for current month
    latest = df.iloc[-1]
    progress = min(latest["actual"] / latest["expected"], 1.0) if latest["expected"] > 0 else 0.0
    st.markdown(f"**Latest Month ({latest['month']}) Progress**")
    st.progress(progress)
    st.caption(
        f"{format_currency(latest['actual'], currency)} of "
        f"{format_currency(latest['expected'], currency)} "
        f"({progress * 100:.1f}%)"
    )

    # Bar chart: Expected vs Actual per month
    fig = go.Figure()
    fig.add_trace(
        go.Bar(x=df["month"], y=df["expected"], name="Expected", marker_color="#4f8ef7")
    )
    fig.add_trace(
        go.Bar(x=df["month"], y=df["actual"], name="Actual", marker_color="#34c97a")
    )
    fig.update_layout(
        barmode="group",
        title="Expected vs Actual Savings",
        xaxis_title="Month",
        yaxis_title=f"Amount ({currency})",
        height=380,
        margin=dict(t=40, b=10, l=10, r=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Surplus line
    df_copy = df.copy()
    df_copy["Surplus"] = df_copy["actual"] - df_copy["expected"]
    fig2 = go.Figure(
        go.Scatter(
            x=df_copy["month"],
            y=df_copy["Surplus"],
            mode="lines+markers",
            fill="tozeroy",
            line=dict(color="#34c97a"),
            fillcolor="rgba(52, 201, 122, 0.15)",
        )
    )
    fig2.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.5)
    fig2.update_layout(
        title="Monthly Surplus / Deficit",
        xaxis_title="Month",
        yaxis_title=f"Surplus ({currency})",
        height=300,
        margin=dict(t=40, b=10, l=10, r=10),
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Raw data table with delete
    st.subheader("📋 Records")
    for _, row in df.iterrows():
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
        c1.write(row["month"])
        c2.write(f"Expected: {format_currency(row['expected'], currency)}")
        c3.write(f"Actual: {format_currency(row['actual'], currency)}")
        surplus = row["actual"] - row["expected"]
        c4.markdown(
            f"{'🟢' if surplus >= 0 else '🔴'} {format_currency(abs(surplus), currency)}"
        )
        if c5.button("🗑", key=f"del_sav_{row['id']}"):
            delete_savings(int(row["id"]), user["id"])
            st.rerun()
