# AI-CRM

AI-CRM is a lightweight, server-rendered customer relationship manager that blends classic lead tracking with automated sentiment analysis. It is designed for simple deployment (SQLite + Flask) while still offering a polished Bootstrap UI, asynchronous AI enrichment, and administrator-only access.

---

## Architecture Overview

- Flask blueprints keep auth and lead management isolated (`app/views/auth.py`, `app/views/leads.py`).
- SQLAlchemy models wrap the SQLite database (default `crm.db`, configurable via `DATABASE_URL`).
- A service layer (`app/services`) hosts the Hugging Face sentiment pipeline and a tiny background task executor so AI work never blocks requests.
- Forms are parsed/validated through dataclasses (`app/forms`) for better structure without a heavyweight form library.
- Templates deliver a responsive Bootstrap experience with list, grid, and kanban views plus a custom delete confirmation modal and spinner/loader states.
- Authentication is session-based; credentials come from environment variables and every lead route is guarded by a `before_request` hook.

```
app/
├── __init__.py          # App factory, config, task system init
├── extensions.py        # Shared SQLAlchemy instance
├── models/lead.py       # Lead ORM definition
├── services/
│   ├── sentiment.py     # Hugging Face integration + async refresh
│   └── tasks.py         # ThreadPool-backed background runner
├── forms/               # Dataclass parsing/validation (auth & leads)
├── views/
│   ├── auth.py          # Login/logout routes
│   └── leads.py         # CRUD, dashboard, status polling endpoint
└── templates/
    ├── layout/base.html # Layout, navbar, flash messaging
    ├── auth/login.html  # Admin login screen
    └── leads/           # Dashboard (list/grid/kanban) & form pages
```

---

## Request Workflow

1. **User submits a lead** from the add/edit form. The route (`app/views/leads.py`) validates input, writes the record, and sets `sentiment="Analyzing"` if notes are present.
2. **Background task enqueued** – instead of blocking the response, the route calls `enqueue_sentiment_refresh`, which schedules `_refresh_lead_sentiment` on the shared `ThreadPoolExecutor` (see `app/services/tasks.py`).
3. **Hugging Face inference** – the worker loads the cached `distilbert-base-uncased-finetuned-sst-2-english` pipeline (`app/services/sentiment.py`) and analyzes the lead notes. The resulting label/score is written back to the database.
4. **Frontend polling** – the dashboard immediately shows an “Analyzing…” badge. JavaScript polls `/leads/status?ids=<ids>` every 5s for leads still in progress. Once a sentiment is available, the UI swaps in the new badge and percentages, then stops polling.
5. **User sees the update** without reloading the page; the summary tiles and kanban/list/grid cards all receive the refreshed sentiment state.

This separation keeps the web response snappy, avoids timeouts on free-tier hosts, and still surfaces AI insights within seconds.

---

## Getting Started

### 1. Clone & Create a Virtual Environment

```bash
git clone https://github.com/Benardo07/ai-crm.git
cd ai-crm
python -m venv .venv
.venv\Scripts\activate  # PowerShell on Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

The requirements file uses the standard PyPI index plus the PyTorch CPU wheel mirror to keep the install Railway-friendly.

### 3. Configure Environment Variables

Copy the example file and edit the real `.env`:

```bash
copy .env.example .env  # Windows
```

Set at minimum:

```
SECRET_KEY=replace-with-strong-secret
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeMe   # or ADMIN_PASSWORD_HASH=...
# Optional database override
DATABASE_URL=sqlite:///crm.db
```

`python-dotenv` auto-loads this file in development; Railway or other hosts can inject the same variables.

### 4. Run the Development Server

```bash
python run.py
```

Browse to `http://localhost:5000/`. The app redirects to `/login`; sign in using the credentials from `.env` to reach the dashboard.

---

## Workflow & Features

- **Lead CRUD** – Add, edit, or delete leads. Forms include a spinner to prevent double submits and the delete action uses a custom modal.
- **AI Sentiment (Async)** – Notes immediately mark the lead as “Analyzing”, returning the HTTP response without waiting for the model. A background thread processes the text, updates the database, and the UI polls `/leads/status` to replace the “Analyzing…” badge with the final sentiment and confidence score.
- **Dashboard Views** – Toggle between list, grid, or kanban layouts. Search, status filters, and sentiment filters update all views client-side.
- **Visual Health Indicators** – Colored pills show sentiment; summary cards surface key counts (positive, neutral, negative).
- **Authentication First** – All lead routes enforce login; the navbar shows the active user and exposes a logout shortcut.

---

## Customising & Deploying

- **Secrets / Credentials** – Always override `SECRET_KEY` and provide real admin credentials via environment variables (`ADMIN_USERNAME`, `ADMIN_PASSWORD` or `ADMIN_PASSWORD_HASH`).
- **Database** – Switch to Postgres or another backend by setting `DATABASE_URL` (fallback: SQLite file).
- **Model Choice** – Change `MODEL_NAME` in `app/services/sentiment.py` if you want an alternative Hugging Face model.
- **Railway/Render** – A `Procfile` is included. Railway can build and run automatically after you set the env vars; Gunicorn command is `gunicorn --bind 0.0.0.0:$PORT run:app`.
- **Scaling AI** – The built-in ThreadPool suits small deployments. If you need more throughput, replace it with Celery, RQ, or a hosted worker.

---

## Handy Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run dev server
python run.py

# Generate a password hash (inside Python shell)
from werkzeug.security import generate_password_hash
generate_password_hash("YourPassword")
```

---

## Notes

- The first sentiment analysis triggers a model download; subsequent requests reuse the cached pipeline.
- `.env` is git-ignored; share `.env.example` for onboarding.
- Console logs (`app.services.sentiment`) show raw model outputs, useful when debugging the AI pipeline.

Enjoy extending AI-CRM—whether you add new automations, more analytics, or a richer notification system, the modular structure keeps changes straightforward. Happy shipping!
