# ReCloud Lead Intelligence

Find companies with **recruitment pain signals**, score them as leads, and generate
**outreach drafts** for a recruitment-automation product.

ReCloud researches public job data and career pages, captures hiring signals
(open jobs, recruiter/TA roles, high-volume roles, urgent hiring, multiple
locations, stale postings, decision-makers), applies a transparent tiered scoring
model, and drafts cold-email / LinkedIn / WhatsApp messages. **No outreach is ever
sent automatically — drafts only.**

## Tech stack

| Layer            | Tech                                              |
|------------------|---------------------------------------------------|
| Frontend         | Next.js 14 (App Router), TypeScript, Tailwind, shadcn-style UI |
| Backend          | FastAPI (Python 3.12), SQLAlchemy 2, Alembic      |
| Database         | PostgreSQL 16                                      |
| Background jobs  | Redis + RQ worker                                 |
| Auth             | JWT (register / login)                            |
| Orchestration    | Docker Compose                                     |

## Features

1. User register / login (JWT)
2. Lead research campaigns with full ICP inputs (industry, region, min employees,
   job/recruiter/high-volume keywords, target decision-maker titles)
3. Company research from public job data & career pages (pluggable integrations,
   deterministic sample fallback so it works out of the box)
4. Hiring-signal capture (open jobs, recruiter/TA, TA-coordinator/ops, high-volume
   roles, urgent keywords, multiple locations, stale jobs, decision-maker)
5. Transparent **tiered scoring** + priority bands (see below)
6. AI outreach generation: pain hypothesis, bandwidth-pressure rationale, buyer
   persona, outreach angle, cold email, LinkedIn message, WhatsApp message
   (OpenAI-compatible API, **falls back to templates** when no key is set)
7. Dashboard with lead stats
8. Leads table with filters, search, sorting, pagination
9. Lead detail page with score breakdown, jobs, signals, decision-maker, AI drafts
10. CSV export
11. Settings page for integration API keys (stored per-account, never returned to the browser)

## Scoring model

Open-jobs points are **tiered** (only the highest matching threshold counts); every
other signal is **additive**:

| Signal                                   | Points |
|------------------------------------------|--------|
| 20+ open jobs                            | +2     |
| 50+ open jobs                            | +3     |
| 100+ open jobs                           | +5     |
| Hiring recruiter / TA                    | +2     |
| Hiring multiple recruiters               | +3     |
| TA coordinator / recruitment ops         | +3     |
| Urgent hiring keywords                   | +1     |
| Multiple locations                       | +2     |
| High-volume roles                        | +3     |
| Decision-maker found                     | +2     |

**Priority bands:** `0–4 Low` · `5–8 Medium` · `9–13 High` · `14+ Very Hot`

## Database tables

`users`, `campaigns`, `company_leads`, `job_postings`, `research_runs`,
`integration_settings`.

## Optional integrations (pluggable, off by default)

- **JobSpy** — public job-board data
- **Firecrawl** — public website / career-page scraping (respects robots.txt)
- **OpenAI-compatible API** — AI generation (template fallback if unset)
- **Reacher / ZeroBounce / Hunter** — email verification
- **n8n / webhook** — export
- **Baserow / Twenty / HubSpot** — CRM sync placeholders

Every integration degrades gracefully: if a key is missing the app keeps working
using the sample/template path. Only public pages are accessed; logins, CAPTCHAs,
paywalls and robots.txt are never bypassed.

---

## Quick start (Docker Compose)

Prerequisites: Docker + Docker Compose.

```bash
# 1. Clone
git clone https://github.com/unime1988/recloud-lead-intelligence.git
cd recloud-lead-intelligence

# 2. Create your env file (defaults work out of the box for local dev)
cp .env.example .env

# 3. Build & start everything (postgres, redis, backend, worker, frontend)
docker compose up --build
```

On startup the backend automatically runs Alembic migrations and seeds **10 demo
leads**. When the stack is up:

- Frontend: http://localhost:3000
- Backend API + docs: http://localhost:8000/docs

**Demo login:** `demo@recloud.app` / `demo1234`

To stop and remove everything (including the database volume):

```bash
docker compose down -v
```

---

## Local development (without Docker)

Run Postgres + Redis via Docker, and the apps on your host.

### Backend

```bash
docker compose up -d postgres redis

cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/recloud_leads"
export REDIS_URL="redis://localhost:6379/0"

alembic upgrade head      # create schema
python -m app.seed        # seed 10 demo leads
uvicorn app.main:app --reload --port 8000   # API on :8000
```

In a second terminal, start the background worker:

```bash
cd backend && source .venv/bin/activate
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/recloud_leads"
export REDIS_URL="redis://localhost:6379/0"
python -m app.worker
```

### Frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev   # UI on :3000
```

---

## Creating a new migration

After changing `backend/app/models.py`:

```bash
cd backend && source .venv/bin/activate
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/recloud_leads"
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Project layout

```
.
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── alembic/            # migrations
│   ├── app/
│   │   ├── api/routes/     # auth, campaigns, leads, dashboard, settings, export
│   │   ├── core/           # scoring, security
│   │   ├── services/       # jobspy, firecrawl, openai, email_verify, crm, research, sample_data
│   │   ├── main.py         # FastAPI app
│   │   ├── worker.py       # RQ worker
│   │   ├── models.py       # SQLAlchemy models
│   │   └── seed.py         # demo data
│   └── requirements.txt
└── frontend/
    └── src/
        ├── app/            # App Router pages (auth, dashboard, campaigns, leads, settings)
        ├── components/     # UI components
        └── lib/            # api client, auth context, types
```

## Notes & guardrails

- No API keys are hardcoded; everything is read from `.env` / per-account settings.
- Outreach is **draft-only** — `ENABLE_OUTREACH_SENDING` defaults to `false`.
- Research uses a deterministic sample generator by default so the app is fully
  functional with zero external accounts. Configure integrations in **Settings**
  to use live data sources.
