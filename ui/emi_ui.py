"""
ui/emi_ui.py
Streamlit UI for the EMI Calculator module.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from modules.emi import calculate_emi, save_emi, get_user_emis, delete_emi, emi_in_gbp
from utils.fx import SUPPORTED_CURRENCIES, format_currency


def render_emi_page(user: dict) -> None:
    st.header("🏦 EMI / Loan Calculator")

    # ── Calculator ───────────────────────────────────────────────────────────
    st.subheader("Calculate Monthly Instalment")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        currency = st.selectbox(
            "Loan Currency",
            SUPPORTED_CURRENCIES,
            index=SUPPORTED_CURRENCIES.index(user.get("currency", "GBP"))
            if user.get("currency", "GBP") in SUPPORTED_CURRENCIES
            else 0,
        )
    with col2:
        principal = st.number_input(
            "Loan Amount", min_value=0.0, value=10000.0, step=500.0, format="%.2f"
        )
    with col3:
        annual_rate = st.number_input(
            "Annual Interest Rate (%)", min_value=0.0, max_value=50.0, value=8.5, step=0.1
        )
    with col4:
        tenure = st.number_input(
            "Tenure (months)", min_value=1, max_value=360, value=24, step=1
        )

    label = st.text_input("Loan Label (optional)", placeholder="e.g. Car Loan")

    if st.button("⚡ Calculate EMI", use_container_width=True):
        if principal <= 0:
            st.error("Loan amount must be greater than zero.")
        else:
            result = calculate_emi(principal, annual_rate, tenure)
            # Store in session state so Save button survives the rerun
            st.session_state["emi_result"] = result
            st.session_state["emi_inputs"] = {
                "principal": principal,
                "annual_rate": annual_rate,
                "tenure": tenure,
                "currency": currency,
                "label": label,
            }

    # ── Show results if available in session state ───────────────────────────
    if "emi_result" in st.session_state:
        result = st.session_state["emi_result"]
        inputs = st.session_state["emi_inputs"]
        _cur = inputs["currency"]
        gbp_emi = emi_in_gbp(result["emi"], _cur)

        # Metric cards
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Monthly EMI", format_currency(result["emi"], _cur))
        m2.metric("EMI in GBP", f"£{gbp_emi:,.2f}")
        m3.metric("Total Payable", format_currency(result["total_payable"], _cur))
        m4.metric(
            "Total Interest",
            format_currency(result["total_interest"], _cur),
            delta=f"{result['total_interest'] / inputs['principal'] * 100:.1f}% extra",
            delta_color="inverse",
        )

        # Pie: principal vs interest
        fig_pie = go.Figure(
            go.Pie(
                labels=["Principal", "Interest"],
                values=[inputs["principal"], result["total_interest"]],
                hole=0.45,
                marker_colors=["#4f8ef7", "#f7874f"],
            )
        )
        fig_pie.update_layout(
            title="Principal vs Interest Breakdown",
            height=320,
            margin=dict(t=40, b=10, l=10, r=10),
        )

        # Balance over time
        schedule = result["schedule"]
        fig_line = go.Figure()
        fig_line.add_trace(
            go.Scatter(
                x=schedule["Month"],
                y=schedule["Balance"],
                mode="lines+markers",
                name="Remaining Balance",
                line=dict(color="#4f8ef7"),
                fill="tozeroy",
                fillcolor="rgba(79, 142, 247, 0.15)",
            )
        )
        fig_line.update_layout(
            title="Loan Balance Over Time",
            xaxis_title="Month",
            yaxis_title=f"Balance ({_cur})",
            height=320,
            margin=dict(t=40, b=10, l=10, r=10),
        )

        chart_col1, chart_col2 = st.columns(2)
        chart_col1.plotly_chart(fig_pie, use_container_width=True)
        chart_col2.plotly_chart(fig_line, use_container_width=True)

        # Amortisation table
        with st.expander("📋 View Full Amortisation Schedule"):
            fmt_schedule = schedule.copy()
            for col in ["EMI", "Principal", "Interest", "Balance"]:
                fmt_schedule[col] = fmt_schedule[col].map(
                    lambda v: format_currency(v, _cur)
                )
            st.dataframe(fmt_schedule, use_container_width=True, hide_index=True)

        # Save — uses session state inputs, NOT the widget values (which reset on rerun)
        if st.button("💾 Save This Loan Record", use_container_width=True):
            res = save_emi(
                user["id"],
                inputs["label"] or f"Loan {inputs['principal']:.0f}",
                inputs["principal"],
                inputs["annual_rate"],
                inputs["tenure"],
                inputs["currency"],
            )
            if res["success"]:
                st.success("Loan saved to your profile!")
                del st.session_state["emi_result"]
                del st.session_state["emi_inputs"]
                st.rerun()
            else:
                st.error(res["error"])

    st.divider()

    # ── Saved loans ──────────────────────────────────────────────────────────
    st.subheader("📂 Saved Loans")
    emis = get_user_emis(user["id"])

    if not emis:
        st.info("No saved loans yet. Calculate an EMI above and save it.")
        return

    for emi_rec in emis:
        result = calculate_emi(
            emi_rec["loan_amount"], emi_rec["interest_rate"], emi_rec["tenure"]
        )
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
        c1.markdown(f"**{emi_rec['label']}**")
        c2.write(format_currency(emi_rec["loan_amount"], emi_rec["currency"]))
        c3.write(f"EMI: {format_currency(result['emi'], emi_rec['currency'])}")
        c4.write(f"{emi_rec['interest_rate']}% / {emi_rec['tenure']}m")
        if c5.button("🗑", key=f"del_emi_{emi_rec['id']}"):
            delete_emi(emi_rec["id"], user["id"])
            st.rerun()