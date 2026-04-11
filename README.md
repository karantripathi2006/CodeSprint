# ResuMatch AI

**Multi-Agent AI System for Intelligent Resume Parsing, Skill Normalization, and Semantic Job Matching**

Built for DA-IICT Hackathon 2026

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     REST API (FastAPI)                    │
│    /parse   /parse/batch   /candidates   /match   /skills│
├──────────────────────────────────────────────────────────┤
│                  Agent Orchestrator                       │
│         (retry logic, batch, error handling)              │
├────────────┬──────────────────┬──────────────────────────┤
│  Resume    │  Skill           │  Semantic                │
│  Parser    │  Normalizer      │  Matcher                 │
│  Agent     │  Agent           │  Agent                   │
├────────────┴──────────────────┴──────────────────────────┤
│  PostgreSQL/SQLite  │  ChromaDB (Vector)  │  Redis/Queue │
└──────────────────────────────────────────────────────────┘
```

**Flow:** Resume Upload → Parsing Agent → Skill Normalization → Semantic Matching → Results

---

## Quick Start (Local)

### Prerequisites

- Python 3.11+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — `pip install uv` or `winget install astral-sh.uv`

### 1. Backend

```bash
uv sync                                      # creates .venv, installs all deps
python init_db.py                            # create SQLite DB + seed skill taxonomy
uv run uvicorn app.main:app --reload         # starts on http://localhost:8000
```

> On first run, `sentence-transformers` downloads the embedding model (~80 MB).

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                                  # starts on http://localhost:5173
```

The Vite dev server proxies `/api/*` to `http://localhost:8000` automatically.

### Useful URLs

| URL | Description |
|-----|-------------|
| http://localhost:5173 | Frontend dashboard |
| http://localhost:8000/docs | Swagger API docs |
| http://localhost:8000/redoc | ReDoc API docs |
| http://localhost:8000/health | Health check |

---

## Docker (Full Stack)

Runs FastAPI + PostgreSQL + Redis together.

```bash
uv lock                        # generate lockfile if not committed yet
docker compose up --build
```

| Service | Port |
|---------|------|
| FastAPI app | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |

---

## Configuration

Copy `.env.example` to `.env` and adjust as needed.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./resumatch.db` | DB connection (SQLite locally, Postgres in Docker) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for async task queue |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `SKILL_WEIGHT` | `0.50` | Weight for skill score |
| `EXPERIENCE_WEIGHT` | `0.30` | Weight for experience score |
| `API_KEY` | `dev-api-key-...` | API authentication key |
| `DEBUG` | `true` | Bypasses auth in dev mode |

---

## API Reference

### Parse a resume
```bash
curl -X POST http://localhost:8000/api/v1/parse \
  -F "file=@resume.pdf"
```

### Match candidate to job
```bash
curl -X POST http://localhost:8000/api/v1/match \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": 1,
    "job_description": {
      "title": "Senior Python Developer",
      "description": "Looking for a Python developer with FastAPI experience",
      "required_skills": ["Python", "FastAPI", "PostgreSQL"],
      "optional_skills": ["Docker", "AWS"],
      "experience_min": 3
    }
  }'
```

### Get candidate skills
```bash
curl http://localhost:8000/api/v1/candidates/1/skills
```

---

## Project Structure

```
.
├── app/
│   ├── main.py               # FastAPI entry point
│   ├── core/                 # Config, database, security
│   ├── models/               # SQLAlchemy models
│   ├── agents/               # Resume parser, skill normalizer, semantic matcher, orchestrator
│   ├── services/             # Embedding & vector store
│   ├── tasks/                # Celery async tasks
│   └── api/v1/               # REST endpoints + Pydantic schemas
├── frontend/                 # React + Vite dashboard (see frontend/README.md)
├── pyproject.toml            # Python project & deps (managed by uv)
├── uv.lock                   # Locked dependency versions
├── requirements.txt          # Used by Docker pip fallback
├── Dockerfile
├── docker-compose.yml
├── init_db.py                # DB init + seed script
└── .env                      # Local environment variables (not committed)
```

---

## Agents

| Agent | Purpose | Key Libraries |
|-------|---------|---------------|
| **Resume Parser** | Extract structured data from PDF/DOCX/TXT | PyMuPDF, pdfplumber, python-docx |
| **Skill Normalizer** | Map skills to taxonomy, resolve synonyms | Custom taxonomy, fuzzy matching |
| **Semantic Matcher** | Score candidates against jobs | sentence-transformers, cosine similarity |
| **Orchestrator** | Coordinate pipeline with retries | Custom pipeline engine |

---

## Team

Built for DA-IICT Hackathon 2026
