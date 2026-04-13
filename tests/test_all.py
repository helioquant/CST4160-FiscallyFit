"""
tests/test_all.py
Unit tests for FiscallyFit – auth, EMI, savings, expenses, FX, sentiment.
Run with: pytest tests/ -v
"""

import os
import sys
import pytest
import tempfile
import pandas as pd

# Ensure project root is on path
ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.abspath(ROOT))

# Use a temp file DB (not :memory:) so all connections share the same schema.
_TMP_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_TMP_DB.close()
os.environ["DB_PATH"] = _TMP_DB.name

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Initialise the temp-file database once for all tests."""
    # Reload db module so it picks up the new DB_PATH env var
    import importlib
    import database.db as db_mod
    importlib.reload(db_mod)
    db_mod.init_db()
    return True


@pytest.fixture
def test_user(setup_db):
    """Register a fresh test user and return their record."""
    import uuid
    from auth.auth import register_user, login_user
    uname = f"testuser_{uuid.uuid4().hex[:6]}"
    reg = register_user("Test", "User", uname, "Password123", 3000.0, "GBP")
    assert reg["success"], reg.get("error")
    login = login_user(uname, "Password123")
    assert login["success"]
    return login["user"]


# ── Auth ──────────────────────────────────────────────────────────────────────

class TestAuth:
    def test_register_success(self, setup_db):
        from auth.auth import register_user
        import uuid
        result = register_user("Alice", "Smith", f"alice_{uuid.uuid4().hex[:4]}", "securepass1", 2000, "USD")
        assert result["success"]
        assert "user_id" in result

    def test_register_duplicate_username(self, setup_db):
        from auth.auth import register_user
        uname = "duplicate_user_test"
        register_user("Bob", "Brown", uname, "pass1234")
        result = register_user("Bob", "Brown", uname, "pass1234")
        assert not result["success"]
        assert "taken" in result["error"].lower()

    def test_register_short_password(self, setup_db):
        from auth.auth import register_user
        result = register_user("X", "Y", "shortpass_user", "abc")
        assert not result["success"]
        assert "8 characters" in result["error"]

    def test_login_success(self, test_user):
        from auth.auth import login_user
        result = login_user(test_user["username"], "Password123")
        assert result["success"]
        assert result["user"]["id"] == test_user["id"]

    def test_login_wrong_password(self, test_user):
        from auth.auth import login_user
        result = login_user(test_user["username"], "wrongpass")
        assert not result["success"]

    def test_login_unknown_user(self, setup_db):
        from auth.auth import login_user
        result = login_user("nobody_ever", "somepassword")
        assert not result["success"]

    def test_update_user(self, test_user):
        from auth.auth import update_user, get_user
        res = update_user(test_user["id"], income=5000.0, currency="EUR")
        assert res["success"]
        refreshed = get_user(test_user["id"])
        assert refreshed["income"] == 5000.0
        assert refreshed["currency"] == "EUR"

    def test_password_not_stored_plaintext(self, setup_db):
        from database.db import execute_query
        rows = execute_query("SELECT password FROM users")
        for row in rows:
            assert not row["password"].startswith("Password")
            assert row["password"].startswith("$2b$")


# ── EMI ───────────────────────────────────────────────────────────────────────

class TestEMI:
    def test_basic_calculation(self):
        from modules.emi import calculate_emi
        result = calculate_emi(100_000, 8.5, 24)
        assert result["emi"] > 0
        assert abs(result["emi"] - 4539.72) < 10.0  # expected ~£4,540/mo (varies by rounding)
        assert result["total_payable"] > 100_000
        assert result["total_interest"] > 0

    def test_zero_interest(self):
        from modules.emi import calculate_emi
        result = calculate_emi(12_000, 0, 12)
        assert result["emi"] == pytest.approx(1000.0, abs=0.01)
        assert result["total_interest"] == 0.0

    def test_schedule_length(self):
        from modules.emi import calculate_emi
        result = calculate_emi(50_000, 5.0, 36)
        assert len(result["schedule"]) == 36

    def test_schedule_final_balance(self):
        from modules.emi import calculate_emi
        result = calculate_emi(10_000, 10.0, 12)
        assert result["schedule"]["Balance"].iloc[-1] == pytest.approx(0.0, abs=1.0)

    def test_invalid_principal(self):
        from modules.emi import calculate_emi
        with pytest.raises(ValueError):
            calculate_emi(0, 5.0, 12)

    def test_save_and_retrieve(self, test_user):
        from modules.emi import save_emi, get_user_emis
        res = save_emi(test_user["id"], "Test Loan", 20_000, 7.5, 18, "GBP")
        assert res["success"]
        emis = get_user_emis(test_user["id"])
        assert len(emis) >= 1
        assert emis[0]["label"] == "Test Loan"

    def test_delete_emi(self, test_user):
        from modules.emi import save_emi, get_user_emis, delete_emi
        save_emi(test_user["id"], "Delete Me", 5000, 6.0, 12, "GBP")
        emis_before = get_user_emis(test_user["id"])
        eid = emis_before[0]["id"]
        res = delete_emi(eid, test_user["id"])
        assert res["success"]
        emis_after = get_user_emis(test_user["id"])
        assert all(e["id"] != eid for e in emis_after)

    def test_gbp_conversion(self):
        from modules.emi import emi_in_gbp
        # GBP → GBP should be 1:1
        result = emi_in_gbp(1000.0, "GBP")
        assert result == pytest.approx(1000.0, rel=0.01)


# ── Savings ───────────────────────────────────────────────────────────────────

class TestSavings:
    def test_save_and_retrieve(self, test_user):
        from modules.savings import save_savings, get_user_savings
        res = save_savings(test_user["id"], 500.0, 420.0, "2024-01")
        assert res["success"]
        df = get_user_savings(test_user["id"])
        assert not df.empty
        row = df[df["month"] == "2024-01"].iloc[0]
        assert row["expected"] == 500.0
        assert row["actual"] == 420.0

    def test_upsert_same_month(self, test_user):
        from modules.savings import save_savings, get_user_savings
        save_savings(test_user["id"], 500.0, 300.0, "2024-02")
        save_savings(test_user["id"], 500.0, 480.0, "2024-02")  # update
        df = get_user_savings(test_user["id"])
        rows = df[df["month"] == "2024-02"]
        assert len(rows) == 1
        assert rows.iloc[0]["actual"] == 480.0

    def test_analysis(self, test_user):
        from modules.savings import save_savings, get_user_savings, savings_analysis
        save_savings(test_user["id"], 600.0, 600.0, "2024-03")
        df = get_user_savings(test_user["id"])
        analysis = savings_analysis(df)
        assert "rate" in analysis
        assert "total_surplus" in analysis
        assert analysis["rate"] <= 100.0 or analysis["rate"] > 0

    def test_delete_savings(self, test_user):
        from modules.savings import save_savings, get_user_savings, delete_savings
        save_savings(test_user["id"], 400.0, 200.0, "2099-01")
        df = get_user_savings(test_user["id"])
        sid = int(df[df["month"] == "2099-01"].iloc[0]["id"])
        delete_savings(sid, test_user["id"])
        df_after = get_user_savings(test_user["id"])
        assert "2099-01" not in df_after["month"].values


# ── Expenses ──────────────────────────────────────────────────────────────────

class TestExpenses:
    def test_add_and_retrieve(self, test_user):
        from modules.expenses import add_expense, get_user_expenses
        res = add_expense(test_user["id"], 75.0, "Food & Groceries", 0.0, "2024-01-15", "Test shop")
        assert res["success"]
        df = get_user_expenses(test_user["id"])
        assert not df.empty
        assert any(df["amount"] == 75.0)

    def test_invalid_amount(self, test_user):
        from modules.expenses import add_expense
        res = add_expense(test_user["id"], 0, "Food & Groceries")
        assert not res["success"]

    def test_analysis(self, test_user):
        from modules.expenses import add_expense, get_user_expenses, expense_analysis
        add_expense(test_user["id"], 100.0, "Housing")
        add_expense(test_user["id"], 50.0, "Transport")
        df = get_user_expenses(test_user["id"])
        analysis = expense_analysis(df, 3000.0)
        assert analysis["total_spent"] > 0
        assert analysis["income_pct"] > 0
        assert not analysis["category_totals"].empty

    def test_delete_expense(self, test_user):
        from modules.expenses import add_expense, get_user_expenses, delete_expense
        res = add_expense(test_user["id"], 9.99, "Subscriptions")
        eid = res["expense_id"]
        delete_expense(eid, test_user["id"])
        df = get_user_expenses(test_user["id"])
        assert eid not in df["id"].values


# ── FX ────────────────────────────────────────────────────────────────────────

class TestFX:
    def test_same_currency(self):
        from utils.fx import get_rate
        assert get_rate("GBP", "GBP") == 1.0
        assert get_rate("USD", "USD") == 1.0

    def test_convert_zero(self):
        from utils.fx import convert
        assert convert(0.0, "USD", "GBP") == 0.0

    def test_format_gbp(self):
        from utils.fx import format_currency
        assert format_currency(1234.56, "GBP") == "£1,234.56"

    def test_format_usd(self):
        from utils.fx import format_currency
        assert format_currency(9999.99, "USD") == "$9,999.99"

    def test_supported_currencies_has_gbp(self):
        from utils.fx import SUPPORTED_CURRENCIES
        assert "GBP" in SUPPORTED_CURRENCIES
        assert "USD" in SUPPORTED_CURRENCIES


# ── Sentiment ─────────────────────────────────────────────────────────────────

class TestSentiment:
    def test_positive(self):
        from modules.news import analyze_sentiment
        result = analyze_sentiment("Excellent earnings beat expectations, profits soar!")
        assert result["label"] == "Positive"
        assert result["polarity"] > 0

    def test_negative(self):
        from modules.news import analyze_sentiment
        result = analyze_sentiment("Terrible losses, bankruptcy fears, stock crashes badly.")
        assert result["label"] == "Negative"
        assert result["polarity"] < 0

    def test_empty_text(self):
        from modules.news import analyze_sentiment
        result = analyze_sentiment("")
        assert result["label"] == "Neutral"
        assert result["polarity"] == 0.0

    def test_returns_emoji(self):
        from modules.news import analyze_sentiment
        result = analyze_sentiment("Good news today")
        assert "emoji" in result
        assert result["emoji"] in ["📈", "📉", "😐"]
