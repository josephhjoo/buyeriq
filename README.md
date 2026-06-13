# BuyerIQ
 
**AI-powered buyer research for M&A sell-side engagements.**
 
Given a target company, BuyerIQ autonomously researches likely acquirers — both strategic buyers and private equity firms — using Claude with live web search, then ranks each contact by a confidence score based on source recency and verifiability. Results are saved per user and exportable as CSV or PDF.
 
🔗 **Live:** [buyeriq-n7wb.onrender.com](https://buyeriq-n7wb.onrender.com)
 
---
 
## What it does
 
When a boutique investment bank runs a sell-side M&A process, an analyst has to build a list of potential buyers and find the right contact at each firm — work that's traditionally done by manually browsing the web and judging how confident they are that each contact is correct and current.
 
BuyerIQ automates that workflow:
 
1. You describe the target company — industry, revenue, geography, and a short description.
2. An AI agent searches the web for PE firms with a relevant mandate, recent comparable acquisitions, and corporate-development contacts at strategic acquirers.
3. Each potential buyer is returned with a rationale, the most relevant contact person, source links, and a **confidence score (0–100)** reflecting how verifiable the contact is.
4. Results are saved to your account and can be exported as a formatted CSV or PDF deal memo.
The confidence score is the core idea — it makes explicit the judgment an analyst would otherwise make in their head, scoring contacts higher when they come from official press releases or firm websites and lower when the source is weak or possibly outdated.
 
---
 
## How it works
 
```
Browser → Flask (gunicorn) → Claude Sonnet + web search tool
                           → PostgreSQL (per-user search history)
```
 
- **Agent** — a single call to Claude Sonnet with the server-side web search tool enabled (up to 10 searches per run). A system prompt defines the confidence-scoring rubric and enforces structured JSON output, which is parsed into ranked buyer records.
- **Backend** — Flask application factory pattern, with authentication (email/password + Google OAuth) via Flask-Login and Authlib. Every search is scoped to the authenticated user.
- **Storage** — SQLAlchemy models (`User`, `Search`, `Buyer`) backed by PostgreSQL in production, SQLite locally.
- **Exports** — CSV via Python's `csv` module, PDF via ReportLab.
---
 
## Tech stack
 
Python · Flask · SQLAlchemy · PostgreSQL · Flask-Login · Authlib · Anthropic API (Claude Sonnet + web search) · ReportLab · Gunicorn
 
---
 
## Running locally
 
```bash
git clone https://github.com/josephhjoo/buyeriq.git
cd buyeriq
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in your values
python3 run.py
```
 
Open http://localhost:5002 and sign up with email and password.
 
### Environment variables
 
| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | Yes | Session signing key. Generate with `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key |
| `DATABASE_URL` | No | Defaults to local SQLite. Set to a PostgreSQL URL in production |
| `GOOGLE_CLIENT_ID` | No | Only needed for Google sign-in |
| `GOOGLE_CLIENT_SECRET` | No | Only needed for Google sign-in |
| `BUYERIQ_TEST_MODE` | No | Set to `1` to return canned data without calling the API (useful for testing) |
 
---
 
## Project structure
 
```
buyeriq/
├── run.py                      # entry point
├── config.py
├── requirements.txt
├── render.yaml                 # Render deployment config
├── app/
│   ├── __init__.py             # Flask factory: auth, OAuth, blueprints
│   ├── models/models.py        # User, Search, Buyer
│   ├── routes/
│   │   ├── api.py              # research + search history + exports
│   │   └── auth.py             # email/password + Google OAuth
│   └── services/
│       ├── buyer_agent.py      # the core agent
│       ├── csv_export.py
│       └── pdf_export.py
└── frontend/templates/         # login, signup, main app
```
 
---
 
## Notes
 
- AI-researched contacts should be verified before outreach — the confidence score and source links are designed to support that, not replace it.
- The hosted demo runs on a free tier and may take ~30 seconds to wake from idle on the first request.
