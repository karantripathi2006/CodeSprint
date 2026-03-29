# 🧠 ResuMatch AI

**Multi-Agent AI System for Intelligent Resume Parsing, Skill Normalization, and Semantic Job Matching**

Built for DA-IICT Hackathon 2026

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     REST API (FastAPI)                    │
│    /parse   /parse/batch   /candidates   /match   /skills│
├──────────────────────────────────────────────────────────┤
│                  Agent Orchestrator                       │
│         (retry logic, batch, error handling)              │
├────────────┬──────────────────┬──────────────────────────┤
│  📄 Resume │  🔧 Skill        │  🎯 Semantic             │
│  Parser    │  Normalizer      │  Matcher                 │
│  Agent     │  Agent           │  Agent                   │
├────────────┴──────────────────┴──────────────────────────┤
│  PostgreSQL/SQLite  │  ChromaDB (Vector)  │  Redis/Queue │
└──────────────────────────────────────────────────────────┘
```

**Flow:** Resume Upload → Parsing Agent → Skill Normalization → Semantic Matching → Results

---

## 🚀 Quick Start (Local — No Docker)

### 1. Install Dependencies

```bash
cd "DA IICT HACKATHON"
pip install -r requirements.txt
```

> **Note:** On first run, the `sentence-transformers` model (~80MB) will be downloaded automatically.

### 2. Initialize Database

```bash
python init_db.py
```

This creates SQLite database and seeds the skill taxonomy + sample jobs.

### 3. Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Access the App

| URL | Description |
|-----|-------------|
| http://localhost:8000/docs | 📖 Swagger API Docs |
| http://localhost:8000/redoc | 📘 ReDoc API Docs |
| http://localhost:8000/frontend/index.html | 🎨 Frontend Dashboard |
| http://localhost:8000/health | ❤️ Health Check |

---

## 🐳 Docker Setup (Full Stack)

```bash
docker-compose up --build
```

This starts: FastAPI app, PostgreSQL, Redis, and Celery worker.

---

## 📡 API Endpoints

### Parse Resume
```bash
# Single resume
curl -X POST http://localhost:8000/api/v1/parse \
  -F "file=@data/sample_resumes/resume_1.txt"

# Batch processing
curl -X POST http://localhost:8000/api/v1/parse/batch \
  -F "files=@data/sample_resumes/resume_1.txt" \
  -F "files=@data/sample_resumes/resume_2.txt"
```

### Get Candidate Skills
```bash
curl http://localhost:8000/api/v1/candidates/1/skills
```

### Match Candidate with Job
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

### Get Skill Taxonomy
```bash
curl http://localhost:8000/api/v1/skills/taxonomy
```

---

## 📂 Project Structure

```
DA IICT HACKATHON/
├── app/
│   ├── main.py               # FastAPI entry point
│   ├── core/                  # Configuration, DB, security
│   ├── models/                # SQLAlchemy models (6 tables)
│   ├── agents/                # AI agents (parser, normalizer, matcher, orchestrator)
│   ├── services/              # Embedding & vector store services
│   ├── tasks/                 # Celery async tasks
│   └── api/v1/                # REST API endpoints + schemas
├── data/                      # Taxonomy, sample resumes & jobs
├── frontend/                  # Web dashboard (HTML/CSS/JS)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── init_db.py
└── README.md
```

---

## 🤖 Agent Details

| Agent | Purpose | Key Tech |
|-------|---------|----------|
| **Resume Parser** | Extract structured data from PDF/DOCX/TXT | PyMuPDF, pdfplumber, python-docx |
| **Skill Normalizer** | Map skills to taxonomy, resolve synonyms | Custom taxonomy, fuzzy matching |
| **Semantic Matcher** | Score candidates against jobs | sentence-transformers, cosine similarity |
| **Orchestrator** | Coordinate pipeline with retries | Custom pipeline engine |

---

## ⚙️ Configuration

All settings in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./resumatch.db` | Database connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for queues |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `SKILL_WEIGHT` | `0.50` | Weight for skill scoring |
| `EXPERIENCE_WEIGHT` | `0.30` | Weight for experience scoring |
| `API_KEY` | `dev-api-key-...` | API authentication key |
| `DEBUG` | `true` | Debug mode (bypasses auth) |

---

## 📊 Example Response

### Parse Result
```json
{
  "status": "success",
  "candidate_id": 1,
  "parsed_data": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-123-4567",
    "skills": ["Python", "FastAPI", "React", "Docker"],
    "experience": [
      {
        "role": "Senior Software Engineer",
        "company": "TechCorp Inc.",
        "duration": "January 2022 - Present"
      }
    ]
  },
  "normalized_skills": {
    "normalized_skills": ["Python", "FastAPI", "React", "Docker"],
    "inferred_skills": ["Web Frameworks", "Deep Learning"],
    "proficiency_map": { "Python": 0.85, "React": 0.7 }
  }
}
```

### Match Result
```json
{
  "overall_score": 78.5,
  "skill_score": 85.0,
  "experience_score": 70.0,
  "semantic_score": 72.3,
  "matching_skills": ["Python", "FastAPI", "PostgreSQL"],
  "missing_skills": ["Kubernetes"],
  "explanation": "✅ Good match (78.5%)...",
  "recommendations": [
    {
      "skill": "Kubernetes",
      "priority": "high",
      "suggestion": "Learn Kubernetes — required skill for the role."
    }
  ]
}
```

---

## 👥 Team

Built for DA-IICT Hackathon 2026
