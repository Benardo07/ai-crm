# AI-CRM

An AI-assisted CRM built with Flask, SQLite, and Hugging Face Transformers. The application lets you capture leads, enrich each interaction with sentiment analysis, and visualize lead health across list, grid, and Kanban views. Authentication gates the dashboard so only the configured admin can access customer data.

---

## Architecture

- **Flask + Blueprints** – Modular server rendered interface (`app/views`) with dedicated blueprints for auth and lead management.
- **SQLite via SQLAlchemy** – Single-file database managed through a `Lead` ORM model (`app/models/lead.py`).
- **Service Layer** – Sentiment analysis service (`app/services/sentiment.py`) wraps a cached Hugging Face `distilbert-base-uncased-finetuned-sst-2-english` pipeline.
- **Forms Package** – Lightweight dataclass-backed parsing and validation (`app/forms`) for both login and lead forms.
- **Bootstrap Frontend** – Responsive templates (`app/templates`) including the multi-view dashboard (list, grid, Kanban) and admin login.
- **Authentication** – Session-based login using environment-configured admin credentials, enforced via `@bp.before_request` guard on lead routes.

```
app/
├── __init__.py          # App factory, config, blueprint wiring
├── extensions.py        # Shared SQLAlchemy instance
├── models/lead.py       # Lead model definition
├── services/sentiment.py# Hugging Face sentiment helper
├── forms/               # Dataclasses & validators for forms
├── views/
│   ├── auth.py          # Login/logout routes
│   └── leads.py         # CRUD + dashboards (protected)
└── templates/
    ├── layout/base.html # Nav, flash messages, container controls
    ├── auth/login.html  # Admin sign-in screen
    └── leads/           # List/Grid/Kanban dashboard & forms
```

---

## Getting Started

### 1. Clone & Create Virtual Environment

```bash
git clone <repo-url>
cd <repo-directory>
python -m venv .venv
.venv\Scripts\activate  # PowerShell on Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Key packages include Flask, Flask-SQLAlchemy, transformers, torch, Gunicorn (for production), and python-dotenv (loads `.env` values automatically).

### 3. Configure Environment

Copy the sample and customize secrets/credentials:

```bash
copy .env.example .env  # Windows
```

Edit `.env` to set:

```
SECRET_KEY=your-strong-secret
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeMe
# or provide ADMIN_PASSWORD_HASH generated via Werkzeug
```

SQLite is the default (`crm.db`). Override via `DATABASE_URL` (or `SQLALCHEMY_DATABASE_URI`) if desired, e.g. `DATABASE_URL=postgresql://user:pass@host/dbname`.

### 4. Initialize & Run

```bash
python run.py
```

Visit `http://localhost:5000/`. You’ll be redirected to `/login`. Sign in with the admin credentials from `.env`, then you can access the lead dashboard.

---

## Usage Highlights

- **Lead Management** – Create, edit, delete leads. Notes run through the sentiment service before saving, populating `sentiment` and `sentiment_score`.
- **AI Insights** – Dashboard surfaces sentiment badges and percentages, plus status counts and lead totals.
- **Multi-View UI** – Switch between list, grid, and Kanban to match your workflow. Filters and search update all views client-side.
- **Authentication** – Login required for any `/leads` route; session info and flash messages appear in the navbar.

---

## Customization & Deployment

- **Admin Credentials** – Change via environment variables (`ADMIN_USERNAME`, `ADMIN_PASSWORD` or `ADMIN_PASSWORD_HASH`).
- **Secret Key** – Always replace the development default with a unique value before deploying (`SECRET_KEY`).
- **Model Choice** – Swap out `MODEL_NAME` in `app/services/sentiment.py` if you prefer a different Hugging Face pipeline.
- **Deployment** – Gunicorn is bundled for WSGI hosting (e.g., Render). Example command: `gunicorn run:app`.
- **Database** – For production, consider Postgres by setting `DATABASE_URL` (alias: `SQLALCHEMY_DATABASE_URI`).

---

## Project Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python run.py

# Generate a password hash (inside Python shell)
from werkzeug.security import generate_password_hash
generate_password_hash("YourPassword")
```

---

## Notes

- Sentiment model download occurs the first time you save a lead with notes.
- `.env` is ignored by git; `.env.example` documents required variables.
- Logging is configured for the sentiment service and will print raw inference results to the console when notes are analyzed.

Feel free to extend the blueprint structure (e.g., adding analytics routes) or plug in new ML services to enrich the CRM further. Happy selling!
