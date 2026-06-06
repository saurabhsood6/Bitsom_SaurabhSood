# BriefAI — AI-Powered Sales Intelligence Agent

BriefAI is an enterprise sales intelligence MVP that automatically generates concise pre-meeting briefs for sales representatives. It aggregates CRM data, recent company news, and AI-generated insights to prepare sales reps for every meeting in 1-2 minutes of reading.

## Features

- **Calendar Integration** — Mock Google/Outlook calendar showing upcoming meetings
- **Pre-Meeting Brief Generator** — AI-powered summaries with company overview, news, CRM context
- **CRM Integration (Lite)** — Mock Salesforce/HubSpot connector with deal stage and interaction history
- **News Aggregation** — Fetches company news via NewsAPI (falls back to curated mock data)
- **Insight Highlighting** — Identifies 1-2 pain points and suggests a conversation angle
- **Notification System** — Delivers briefs via console output or SMTP email
- **Web Dashboard** — Clean FastAPI + Jinja2 dashboard with meeting cards and brief detail views

## Quick Start

```bash
# 1. Navigate to the project directory
cd briefai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 4. Start the server
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000` to open the dashboard.

## Project Structure

```
briefai/
├── main.py                    # FastAPI app entry point
├── agents/
│   ├── brief_generator.py     # Core brief generation (calls Claude)
│   ├── news_aggregator.py     # News fetching + mock data
│   ├── insight_engine.py      # Pain points & conversation angle
│   └── crm_connector.py       # Mock CRM integration
├── integrations/
│   ├── calendar_mock.py       # Mock calendar integration
│   └── notification.py        # Email/console notifications
├── models/
│   └── schemas.py             # Pydantic models
├── db/
│   └── database.py            # SQLite setup and CRUD
├── templates/
│   ├── dashboard.html         # Main dashboard
│   └── brief.html             # Brief detail view
├── static/
│   └── style.css              # Dashboard styling
├── requirements.txt
├── .env.example
└── README.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Dashboard (HTML) |
| GET | `/meetings/{id}/brief` | Brief detail page (HTML) |
| POST | `/meetings/{id}/generate-brief` | Trigger brief generation |
| GET | `/api/meetings` | List all meetings (JSON) |
| GET | `/api/meetings/{id}` | Get single meeting (JSON) |
| POST | `/api/notify` | Send brief notification |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Recommended | Enables AI brief generation via Claude |
| `NEWSAPI_KEY` | Optional | Enables real news fetching |
| `SMTP_HOST/USER/PASS` | Optional | Enables email notifications |

Without `ANTHROPIC_API_KEY`, the app falls back to a rule-based brief generator.

## Tech Stack

- **Python 3.11** with FastAPI
- **Claude claude-haiku-4-5** (Anthropic SDK) for AI summarization
- **SQLite** for brief and meeting storage
- **Jinja2** for HTML templates
- **Pydantic v2** for data validation
