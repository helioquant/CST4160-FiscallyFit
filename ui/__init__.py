from .dashboard import render_dashboard
from .auth_ui import render_auth_page, render_profile_page
from .emi_ui import render_emi_page
from .savings_ui import render_savings_page
from .stocks_ui import render_stocks_page
from .news_ui import render_news_page
from .expenses_ui import render_expenses_page

__all__ = [
    "render_dashboard",
    "render_auth_page",
    "render_profile_page",
    "render_emi_page",
    "render_savings_page",
    "render_stocks_page",
    "render_news_page",
    "render_expenses_page",
]
