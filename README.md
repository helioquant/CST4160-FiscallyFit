# CST4160-FiscallyFit

<div align="center">

# 💪 FiscallyFit

**Get your finances in shape.**

*A comprehensive Personal Financial Management Dashboard for students and young professionals*

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![AWS](https://img.shields.io/badge/AWS-Deployed-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)](https://aws.amazon.com)
[![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/features/actions)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

[![MDX](https://img.shields.io/badge/Middlesex%20University-CST4160%20Advanced%20Software%20Development%20for%20FinTech-CC0000?style=flat-square)](https://mdx.ac.uk)
[![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen?style=flat-square)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen?style=flat-square)](CONTRIBUTING.md)


[✨ Features](#-features) · [🛠 Installation](#-getting-started) · [📖 Docs](#-project-structure) · [👥 Team](#-team)· [💡 Request Feature](issues)

</div>

---

## 📋 Table of Contents

- [About the Project](#-about-the-project)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running Locally](#running-locally)
- [Environment Variables](#-environment-variables)
- [Project Structure](#-project-structure)
- [Database Schema](#-database-schema)
- [API Integrations](#-api-integrations)
- [Testing](#-testing)
- [CI/CD Pipeline](#-cicd-pipeline)
- [Deployment](#-deployment)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [Academic Context](#-academic-context)
- [License](#-license)

---

## 🧠 About the Project

**FiscallyFit** is an open-source, Python-powered Personal Financial Management (PFM) dashboard designed specifically for **students and young professionals** who want to take control of their finances without the complexity, cost, or intimidation of traditional financial tools.

The application consolidates six core financial management needs into a single, intuitive interface — tracking daily spending, monitoring investment portfolios, converting currencies in real-time, calculating loan repayments, setting savings goals, and staying informed with curated FinTech news.

### 🎯 Who Is This For?

| User Type | How FiscallyFit Helps |
|---|---|
| 🎓 University Students | Track spending, split rent, set savings goals for tuition |
| 💼 Young Professionals | Monitor salary, investments, and loan repayments in one place |
| ✈️ International Users | Multi-currency support with real-time forex conversion |
| 📈 Beginner Investors | Portfolio tracker with plain-English performance metrics |

### 💡 Why FiscallyFit?

Most personal finance apps are either too complex, subscription-based, or locked to a single country's banking system. FiscallyFit is:

- **Free & open-source** — no subscriptions, no paywalls
- **Privacy-first** — your data stays local unless you choose to deploy
- **Globally accessible** — multi-currency and multi-market support from day one
- **Student-built** — designed by people who actually understand broke student life

---

## ✨ Features

<details>
<summary><b>💸 1. Personal Expense Tracker & Analysis</b></summary>

Track every penny. Understand every pattern.

**Data Storage & Input**
- SQLite database with indexed tables for fast querying across large transaction histories
- Manual entry form: date, amount, category, merchant, tags, currency, notes
- Bulk CSV/Excel import with an intelligent column-mapping UI
- Optional bank CSV export integration (Plaid/TrueLayer planned for v2)

**Categorisation**
- Predefined category library with custom category support
- Rule-based auto-categorisation engine using merchant name patterns
- ML classifier (logistic regression) to auto-tag new transactions *(v2)*

**Visualisation & Analytics**
- Monthly spending line chart with rolling averages
- Category breakdown bar chart and donut chart
- Weekday vs. hour heatmap calendar
- Budget variance dashboard: actual vs. target per category
- Anomaly detection using z-scores to flag unusual transactions
- Predictive cashflow projections using time-series analysis *(v2)*

**Alerts**
- Email/Telegram notifications when a category exceeds budget threshold *(v2)*

</details>

<details>
<summary><b>💱 2. Real-Time Forex & Currency Conversion</b></summary>

Live rates. Instant conversions. No surprises.

**Data Sources**
- Primary: [FCS API](https://fcsapi.com) for live and historical FX rates
- Fallback: [ForexRateAPI](https://forexrateapi.com)
- Rates cached in `st.session_state` and local SQLite table `fx_cache` to reduce API calls

**Conversion Engine**
- Base-currency normalisation across all modules (expenses, portfolio, goals)
- Supports 150+ currency pairs including major, minor, and exotic pairs
- Historical FX chart with selectable date ranges

**User Personalisation**
- Set a home base currency that drives all app-wide calculations
- Watchlist for monitored currency pairs
- Rate threshold alerts: notify when EUR/USD crosses X *(v2)*

</details>

<details>
<summary><b>🏦 3. Loan & Credit Card EMI Calculator</b></summary>

Know exactly what you owe and when you'll be free.

**Calculation Logic**
- Standard amortising loan formula: `EMI = P × r(1+r)ⁿ / ((1+r)ⁿ - 1)`
- Supports: fixed-rate loans, interest-only periods, extra payments
- Credit card mode: fixed payment vs minimum payment (% of balance) payoff simulation
- Multiple loan types: home, auto, personal, education, credit card

**User Input & Validation**
- Friendly slider and input UI for principal, APR, tenure, and frequency
- Input validation: enforced APR limits, positive amounts, realistic tenure ranges
- Toggle between Loan mode and Credit Card mode

**Visualisation**
- Line chart: remaining balance over time
- Stacked area chart: principal vs interest breakdown per period
- Summary KPIs: total interest paid, payoff date, interest saved with extra payments
- Side-by-side loan scenario comparison with overlaid charts

</details>

<details>
<summary><b>📈 4. Asset Portfolio Tracker (Stocks / Crypto / Futures)</b></summary>

One dashboard for every market you touch.

**Data Sources**
- Equities & ETFs: `yfinance` (Yahoo Finance)
- Cryptocurrency: Binance API / CoinGecko
- Futures & derivatives: Alpha Vantage *(extensible)*
- All positions and trades stored in SQLite: `trades`, `positions`, `watchlist`

**Portfolio Management**
- Manual trade entry: date, symbol, quantity, price, fees, buy/sell side
- CSV import from major brokers (Interactive Brokers, Robinhood format)
- Holdings with average cost basis, unrealised P/L, realised P/L
- Running portfolio time-series with cash flow tracking

**Performance Metrics**
- Daily and cumulative returns
- Volatility (annualised standard deviation)
- Maximum drawdown
- Benchmark comparison (vs SPY or custom index)
- Asset allocation breakdown by class, sector, and region

**Visualisation**
- Portfolio value vs benchmark line chart
- Allocation pie chart and sector bar chart
- Scatter plot: return vs volatility per asset

</details>

<details>
<summary><b>🎯 5. Savings Goal Tracker</b></summary>

Set it. Track it. Celebrate it.

**Goal Setting**
- Create goals with: name, target amount, target date, currency, initial amount, contribution frequency
- Link goals to expense surplus detected automatically by the analytics engine

**Projection Logic**
- Compute required periodic contribution given target and time horizon
- Given fixed contribution, calculate expected completion date
- Assumes configurable expected return rate (0% to custom % annually)
- Monte Carlo simulation for probability of success under return distribution *(v2)*

**Visualisation**
- Progress bar: current savings vs target
- Dual projection chart: current pace vs required pace
- Multi-goal stacked view showing total monthly commitment
- Goal completion calendar

**Gamification**
- Contribution streak counter
- Milestone badges (25%, 50%, 75%, 100%)
- Completion celebration animation *(v2)*

</details>

<details>
<summary><b>📰 6. FinTech News Dashboard</b></summary>

Stay informed. Invest smarter.

**Data Sources**
- [NewsAPI](https://newsapi.org) for broad financial news
- [Finnhub](https://finnhub.io) for market-specific news
- RSS feeds from curated FinTech sources
- News cached in SQLite `news_cache` table by topic hash and timestamp

**Personalisation**
- Tabs: General FinTech | Crypto | My Portfolio | FX Markets
- Portfolio tab auto-generates queries from your actual holdings (e.g., `"AAPL OR V OR BTC"`)
- User-defined source whitelist, region filter, and topic tags

**Sentiment Analysis**
- TextBlob NLP on article titles and descriptions
- Labels: 🟢 Positive / 🟡 Neutral / 🔴 Negative
- "Risk Radar" widget: counts negative news hits for your held assets

</details>

---

## 🏗 Architecture

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        User Browser                          │
└──────────────────────────┬──────────────────────────────────┘
                           │  HTTPS
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                        │
│  ┌──────────┐ ┌────────┐ ┌───────┐ ┌────────┐ ┌────────┐  │
│  │ Expenses │ │ Forex  │ │ Loans │ │Portfol.│ │  News  │  │
│  └────┬─────┘ └───┬────┘ └───┬───┘ └───┬────┘ └───┬────┘  │
└───────┼───────────┼──────────┼──────────┼──────────┼────────┘
        │           │          │          │          │
        └───────────┴──────────┴──────────┴──────────┘
                              │
                    ┌─────────▼──────────┐
                    │    Service Layer    │
                    │  (Business Logic)   │
                    └────┬──────────┬────┘
                         │          │
            ┌────────────▼──┐  ┌────▼────────────────┐
            │   db.py       │  │   External APIs      │
            │  (SQLite)     │  │  ┌──────────────┐   │
            │               │  │  │ FCS Forex    │   │
            │  ┌──────────┐ │  │  │ yfinance     │   │
            │  │expenses  │ │  │  │ NewsAPI      │   │
            │  │portfolio │ │  │  │ Finnhub      │   │
            │  │goals     │ │  │  │ Binance      │   │
            │  │fx_cache  │ │  │  └──────────────┘   │
            │  │news_cache│ │  └────────────────────────┘
            │  └──────────┘ │
            └───────────────┘
                    │
        ┌───────────▼──────────────┐
        │    Visualisation Layer    │
        │   Plotly · Altair · st   │
        └──────────────────────────┘
```

### Module Communication Flow

```
User Settings (base currency, risk profile, theme)
        │
        ├──▶ Forex Module ──▶ normalises currencies ──▶ Expenses Module
        │                                           ──▶ Portfolio Module
        │                                           ──▶ Goals Module
        │
        ├──▶ Portfolio Module ──▶ ticker watchlist ──▶ News Dashboard
        │
        ├──▶ Loan Module ──▶ debt payoff target ──▶ Savings Goals
        │
        └──▶ Expense Analytics ──▶ surplus detection ──▶ Savings Goals
```

---

## 🛠 Tech Stack

### Core

| Layer | Technology | Purpose |
|---|---|---|
| Frontend / UI | [Streamlit 1.x](https://streamlit.io) | Single-page dashboard with sidebar navigation |
| Backend | Python 3.10+ | Business logic and service layer |
| Database | SQLite | Local persistent storage for all user data |
| Data Processing | Pandas, NumPy | DataFrame manipulation, analytics |
| Visualisation | Plotly Express, Altair | Interactive charts and graphs |

### APIs & External Services

| Service | Provider | Use Case |
|---|---|---|
| Forex Rates | FCS API / ForexRateAPI | Live and historical exchange rates |
| Stock / ETF Data | yfinance | Equity and ETF price history |
| Crypto Data | Binance API / CoinGecko | Cryptocurrency prices |
| Financial News | NewsAPI, Finnhub | News aggregation and filtering |
| NLP Sentiment | TextBlob | News sentiment scoring |

### DevOps & Infrastructure

| Tool | Purpose |
|---|---|
| GitHub Actions | CI/CD — automated testing and deployment |
| AWS Elastic Beanstalk | Cloud hosting and scalability |
| pytest + pytest-cov | Unit testing and coverage reporting |
| python-dotenv | Environment variable management |
| Git | Version control and collaborative development |

---

## 🚀 Getting Started

### Prerequisites

Ensure you have the following installed:

```bash
python --version    # Python 3.10 or higher required
pip --version       # pip 22+ recommended
git --version       # any recent version
```

You will also need API keys for:
- [FCS API](https://fcsapi.com) — Forex rates (free tier available)
- [NewsAPI](https://newsapi.org) — News aggregation (free tier available)
- [Finnhub](https://finnhub.io) — Financial news (free tier available)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/fiscallyfit.git
cd fiscallyfit

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the virtual environment
source venv/bin/activate          # macOS / Linux
venv\Scripts\activate             # Windows (Command Prompt)
.\venv\Scripts\Activate.ps1       # Windows (PowerShell)

# 4. Install all dependencies
pip install -r requirements.txt

# 5. Configure environment variables
cp .env.example .streamlit/secrets.toml
# Open secrets.toml and add your API keys

# 6. Initialise the database
python db.py

# 7. Launch the application
streamlit run app.py
```

The app will open automatically at `http://localhost:8501`

### Running Locally

```bash
# Standard run
streamlit run app.py

# Run on a specific port
streamlit run app.py --server.port 8080

# Run in headless mode (for servers)
streamlit run app.py --server.headless true
```

---

## 🔑 Environment Variables

Create `.streamlit/secrets.toml` in the project root (this file is gitignored):

```toml
# Forex
FOREX_API_KEY        = "your_fcs_api_key_here"
FOREX_FALLBACK_KEY   = "your_forexrateapi_key_here"

# News
NEWS_API_KEY         = "your_newsapi_key_here"
FINNHUB_API_KEY      = "your_finnhub_key_here"

# App
SECRET_KEY           = "a_random_secret_string_for_sessions"
DEFAULT_CURRENCY     = "GBP"
DEBUG                = false
```

> ⚠️ **Security note:** Never commit API keys or secrets to version control. `.streamlit/secrets.toml` is included in `.gitignore` by default.

---

## 🗃 Database Schema

FiscallyFit uses **SQLite** with the following core tables:

```sql
-- User settings (persisted preferences)
CREATE TABLE user_settings (
    user_id       TEXT PRIMARY KEY,
    base_currency TEXT DEFAULT 'GBP',
    risk_profile  TEXT DEFAULT 'moderate',
    theme         TEXT DEFAULT 'light',
    updated_at    TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Expense transactions
CREATE TABLE expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT,
    date        TEXT,
    amount      REAL,
    currency    TEXT,
    category    TEXT,
    merchant    TEXT,
    tags        TEXT,
    notes       TEXT,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_expenses_user_date ON expenses(user_id, date);
CREATE INDEX idx_expenses_category  ON expenses(user_id, category);

-- Asset trades
CREATE TABLE trades (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    TEXT,
    date       TEXT,
    ticker     TEXT,
    side       TEXT,   -- 'BUY' or 'SELL'
    quantity   REAL,
    price      REAL,
    fees       REAL DEFAULT 0,
    currency   TEXT
);

-- Savings goals
CREATE TABLE goals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         TEXT,
    name            TEXT,
    target_amount   REAL,
    current_amount  REAL DEFAULT 0,
    target_date     TEXT,
    currency        TEXT,
    contribution    REAL,
    frequency       TEXT,   -- 'monthly', 'weekly', etc.
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Forex rate cache
CREATE TABLE fx_cache (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    base       TEXT,
    symbols    TEXT,
    rates      TEXT,   -- JSON blob
    fetched_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔌 API Integrations

| API | Endpoint | Auth | Free Tier | Used For |
|---|---|---|---|---|
| FCS API | `fcsapi.com/api/forex/latest` | API Key | 500 req/month | Live FX rates |
| ForexRateAPI | `api.forexrateapi.com/v1/latest` | API Key | 100 req/month | FX fallback |
| yfinance | Yahoo Finance (unofficial) | None | Unlimited | Stock/ETF data |
| Binance | `api.binance.com/api/v3` | Optional | Generous | Crypto prices |
| NewsAPI | `newsapi.org/v2/everything` | API Key | 100 req/day | News articles |
| Finnhub | `finnhub.io/api/v1/news` | API Key | 60 req/min | Market news |

All external calls include timeout handling, retry logic, and graceful fallback messaging.

---

## 🧪 Testing

FiscallyFit uses **pytest** with a focus on testing all core business logic in the service layer.

```bash
# Run the full test suite
pytest

# Run with detailed output
pytest -v

# Run with coverage report
pytest --cov=services --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=services --cov-report=html
open htmlcov/index.html

# Run a specific module's tests
pytest tests/test_loans.py -v

# Run tests matching a keyword
pytest -k "forex" -v
```

### Test Coverage Targets

| Module | Coverage Target | Test Focus |
|---|---|---|
| `services/loans.py` | 95%+ | EMI accuracy, edge cases (0% APR, extra payments) |
| `services/forex.py` | 90%+ | Conversion logic with mocked API responses |
| `services/goals.py` | 90%+ | Projection maths, boundary conditions |
| `services/expenses.py` | 85%+ | CRUD operations, filtering, budget variance |
| `services/portfolio.py` | 80%+ | P&L calculations, metric computations |

---

## ⚙️ CI/CD Pipeline

Every push and pull request triggers the automated pipeline via **GitHub Actions**:

```
Push to any branch
        │
        ▼
  ┌─────────────────┐
  │  Lint (flake8)  │ ── fail → block merge
  └────────┬────────┘
           │ pass
           ▼
  ┌─────────────────┐
  │  Unit Tests     │ ── fail → block merge
  │  (pytest)       │
  └────────┬────────┘
           │ pass
           ▼
  ┌─────────────────┐
  │ Coverage Check  │ ── below 80% → warning
  │ (pytest-cov)    │
  └────────┬────────┘
           │
           ▼ (main branch only)
  ┌─────────────────┐
  │  Deploy to AWS  │
  │ Elastic Beanst. │
  └─────────────────┘
```

CI configuration: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

---

## ☁️ Deployment

FiscallyFit is deployed on **AWS Elastic Beanstalk** with automatic deployments triggered from the `main` branch.

```bash
# Install the AWS EB CLI
pip install awsebcli

# Initialise the application (first time only)
eb init fiscallyfit \
  --platform python-3.10 \
  --region eu-west-1

# Create the environment (first time only)
eb create fiscallyfit-production \
  --instance-type t3.micro \
  --single

# Deploy updates
eb deploy

# View application status
eb status

# Stream live logs
eb logs --all
```


---

## 🤝 Contributing

Contributions are warmly welcome! Here's how to get involved:

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/your-username/fiscallyfit.git

# 3. Create a feature branch
git checkout -b feature/your-feature-name

# 4. Make your changes and write tests

# 5. Ensure all tests pass
pytest

# 6. Commit with a clear message
git commit -m "feat: add savings goal Monte Carlo simulation"

# 7. Push to your fork
git push origin feature/your-feature-name

# 8. Open a Pull Request on GitHub
```

Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) for our full contribution guidelines, code style standards, and branch naming conventions.

---

## 📚 Academic Context

This project was developed as the summative assessment for:

| **Module** | CST4160 — Advanced Software Development for Financial Technology |
| **University** | Middlesex University London |
| Term 2, 2025/2026 |
| **Submission** | 10th April 2026 |
| **Module Leader (Hendon)** | Dr. Stephen E. Agada |
---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for full details.

```
MIT License — Copyright (c) 2026 FiscallyFit Team
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software to deal in the Software without restriction.
```

---

<div align="center">

**💪 FiscallyFit** — *Get your finances in shape.*

Built with ☕, Python, and the lived experience of being a broke student.

*CST4160 · Middlesex University · 2025/2026*

⭐ **Star this repo if FiscallyFit helped you understand where your money actually goes** ⭐

</div>
