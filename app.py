"""
app.py
FiscallyFit – Streamlit application entry point.

Run with:
    streamlit run app.py
"""

import logging
import os
import sys

import streamlit as st
from dotenv import load_dotenv

# ── Path setup ────────────────────────────────────────────────────────────────
# Ensure the project root is on sys.path so absolute imports work regardless of
# how Streamlit is invoked.
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── Environment & logging ─────────────────────────────────────────────────────
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Streamlit page config (MUST be first Streamlit call) ─────────────────────
st.set_page_config(
    page_title="FiscallyFit",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Lazy imports (after path setup) ──────────────────────────────────────────
from database.db import init_db
from ui.auth_ui import render_auth_page, render_profile_page
from ui.dashboard import render_dashboard
from ui.emi_ui import render_emi_page
from ui.savings_ui import render_savings_page
from ui.stocks_ui import render_stocks_page
from ui.news_ui import render_news_page
from ui.expenses_ui import render_expenses_page

# ── DB initialisation (runs once per worker process) ─────────────────────────
@st.cache_resource
def _init_database():
    init_db()
    logger.info("Database ready.")

_init_database()

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        /* Sidebar branding */
        [data-testid="stSidebar"] { background: #0e1117; }
        [data-testid="stSidebar"] * { color: #e0e0e0 !important; }

        /* Metric cards */
        [data-testid="metric-container"] {
            background: #1a1d27;
            border: 1px solid #2a2d3a;
            border-radius: 10px;
            padding: 12px 16px;
        }

        /* Buttons */
        .stButton > button {
            border-radius: 8px;
            font-weight: 600;
        }
        .stButton > button:hover {
            border-color: #34c97a;
            color: #34c97a;
        }

        /* Hide Streamlit footer */
        footer { visibility: hidden; }
        #MainMenu { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session defaults ───────────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state["user"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "Dashboard"

# ── Auth gate ─────────────────────────────────────────────────────────────────
user = st.session_state["user"]

if user is None:
    render_auth_page()
    st.stop()

# ── Sidebar navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style='text-align:center; padding:1rem 0 0.5rem;'>
            <span style='font-size:2rem;'>💚</span>
            <h2 style='margin:0; font-size:1.4rem;'>FiscallyFit</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    pages = {
        "🏠 Dashboard": "Dashboard",
        "💳 Expenses": "Expenses",
        "💰 Savings": "Savings",
        "📈 Stocks": "Stocks",
        "🏦 EMI Calculator": "EMI Calculator",
        "📰 News": "News",
        "👤 Profile": "Profile",
    }

    for label, page_key in pages.items():
        is_active = st.session_state["page"] == page_key
        btn_type = "primary" if is_active else "secondary"
        if st.button(label, use_container_width=True, type=btn_type, key=f"nav_{page_key}"):
            st.session_state["page"] = page_key
            st.rerun()

    st.divider()
    st.caption(f"👋 {user['first_name']} {user['last_name']}")
    st.caption(f"💱 {user.get('currency', 'GBP')}  ·  💼 {user['username']}")

    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ── Page routing ───────────────────────────────────────────────────────────────
page = st.session_state["page"]
user = st.session_state["user"]   # re-read after potential profile update

match page:
    case "Dashboard":
        render_dashboard(user)
    case "Expenses":
        render_expenses_page(user)
    case "Savings":
        render_savings_page(user)
    case "Stocks":
        render_stocks_page(user)
    case "EMI Calculator":
        render_emi_page(user)
    case "News":
        render_news_page(user)
    case "Profile":
        render_profile_page(user)
    case _:
        st.error(f"Unknown page: {page}")
        st.session_state["page"] = "Dashboard"
        st.rerun()
