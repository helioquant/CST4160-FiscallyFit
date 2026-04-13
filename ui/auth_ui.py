"""
ui/auth_ui.py
Streamlit login / registration UI.
"""

import streamlit as st
from auth.auth import register_user, login_user
from utils.fx import SUPPORTED_CURRENCIES


def render_auth_page() -> None:
    """Render the unauthenticated landing page with login/register tabs."""
    st.markdown(
        """
        <div style='text-align:center; padding: 2rem 0 1rem 0;'>
            <h1 style='font-size:2.8rem; font-weight:800;'>💚 FiscallyFit</h1>
            <p style='color:#888; font-size:1.1rem;'>
                Your personal finance dashboard — EMI, savings, stocks & more.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs(["🔑 Sign In", "✏️ Create Account"])

    with tab_login:
        _login_form()

    with tab_register:
        _register_form()


def _login_form() -> None:
    with st.form("login_form", clear_on_submit=False):
        st.subheader("Welcome back")
        username = st.text_input("Username", placeholder="your_username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In", use_container_width=True)

    if submitted:
        if not username or not password:
            st.error("Please enter both username and password.")
            return
        result = login_user(username, password)
        if result["success"]:
            st.session_state["user"] = result["user"]
            st.session_state["page"] = "Dashboard"
            st.success(f"Welcome back, {result['user']['first_name']}!")
            st.rerun()
        else:
            st.error(result["error"])


def _register_form() -> None:
    with st.form("register_form", clear_on_submit=True):
        st.subheader("Create your account")
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name")
        with col2:
            last_name = st.text_input("Last Name")

        username = st.text_input("Username", placeholder="must be unique")
        password = st.text_input("Password", type="password", help="Minimum 8 characters")
        confirm = st.text_input("Confirm Password", type="password")

        col3, col4 = st.columns(2)
        with col3:
            income = st.number_input(
                "Monthly Income", min_value=0.0, value=3000.0, step=100.0, format="%.2f"
            )
        with col4:
            currency = st.selectbox(
                "Primary Currency",
                SUPPORTED_CURRENCIES,
                index=SUPPORTED_CURRENCIES.index("GBP"),
            )

        submitted = st.form_submit_button("Create Account", use_container_width=True)

    if submitted:
        if password != confirm:
            st.error("Passwords do not match.")
            return
        result = register_user(first_name, last_name, username, password, income, currency)
        if result["success"]:
            # Auto-login
            login_result = login_user(username, password)
            if login_result["success"]:
                st.session_state["user"] = login_result["user"]
                st.session_state["page"] = "Dashboard"
                st.success("Account created! Welcome to FiscallyFit 🎉")
                st.rerun()
        else:
            st.error(result["error"])


def render_profile_page(user: dict) -> None:
    """User profile / settings page."""
    from auth.auth import update_user, get_user

    st.header("👤 Profile & Settings")

    with st.form("profile_form"):
        st.subheader("Update Profile")
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name", value=user["first_name"])
        with col2:
            last_name = st.text_input("Last Name", value=user["last_name"])

        col3, col4 = st.columns(2)
        with col3:
            income = st.number_input(
                "Monthly Income",
                min_value=0.0,
                value=float(user.get("income", 0.0)),
                step=100.0,
                format="%.2f",
            )
        with col4:
            from utils.fx import SUPPORTED_CURRENCIES
            curr_idx = (
                SUPPORTED_CURRENCIES.index(user.get("currency", "GBP"))
                if user.get("currency", "GBP") in SUPPORTED_CURRENCIES
                else 0
            )
            currency = st.selectbox("Primary Currency", SUPPORTED_CURRENCIES, index=curr_idx)

        st.subheader("Change Password (optional)")
        new_password = st.text_input("New Password", type="password", help="Leave blank to keep current")
        confirm_password = st.text_input("Confirm New Password", type="password")

        save_btn = st.form_submit_button("💾 Save Changes", use_container_width=True)

    if save_btn:
        if new_password and new_password != confirm_password:
            st.error("Passwords do not match.")
            return

        kwargs = dict(
            first_name=first_name,
            last_name=last_name,
            income=income,
            currency=currency,
        )
        if new_password:
            kwargs["new_password"] = new_password

        result = update_user(user["id"], **kwargs)
        if result["success"]:
            # Refresh session user
            refreshed = get_user(user["id"])
            if refreshed:
                st.session_state["user"] = refreshed
            st.success("Profile updated successfully!")
            st.rerun()
        else:
            st.error(result["error"])

    st.divider()

    st.subheader("Account Info")
    st.write(f"**Username:** {user['username']}")
    st.write(f"**Member since:** {user.get('created_at', 'N/A')[:10]}")
    st.write(f"**User ID:** {user['id']}")

    st.divider()
    if st.button("🚪 Sign Out", type="secondary"):
        st.session_state.clear()
        st.rerun()
