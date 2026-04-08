# PriorityPulse-AI

## Overview
PriorityPulse-AI is a Python-based complaint prioritization system that combines NLP, rule-based AI, and explainable scoring to identify urgent or high-impact customer issues. It is designed as a prototype for a support operations dashboard that highlights critical complaints and explains why they should be escalated.

## Current Status
- Backend API built with FastAPI
- Complaint persistence via SQLAlchemy
- NLP preprocessing using spaCy
- Rule-based analysis and explainability pipeline
- Priority scoring implementation
- Static dashboard placeholder included
- Basic tests available

## Tech Stack
- Python 3.10+
- FastAPI
- SQLAlchemy
- spaCy
- SQLite (local prototype)
- Uvicorn

## Repository Structure
```
PriorityPulse-AI/
├── app/
│   ├── api/
│   │   └── routes.py
│   ├── db/
│   │   └── database.py
│   ├── models/
│   │   ├── complaint.py
│   │   └── priority.py
│   ├── schemas/
│   │   ├── request.py
│   │   └── response.py
│   ├── services/
│   │   ├── explainability.py
│   │   ├── llm_engine.py
│   │   ├── nlp.py
│   │   └── scoring.py
│   └── main.py
├── dashboard.html
├── requirements.txt
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── docs/
│   └── branching-and-workflow.md
├── test_api.py
└── test_classification.py
```

## Setup
1. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate # macOS/Linux
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Download the spaCy model:

```bash
python -m spacy download en_core_web_sm
```

4. Run the app:

```bash
uvicorn app.main:app --reload --port 8000
```

5. Open the dashboard at:

```text
http://localhost:8000/dashboard-page
```

## API Endpoints
- `POST /complaints` — create a complaint
- `POST /analyse` — generate urgency, impact, systemic risk
- `POST /score` — compute score and escalation outcome
- `GET /dashboard-page` — serve the dashboard page

## Contribution Workflow
This repository is organized for collaborative development across three contributors.

### Branch strategy
- `main`: production-ready code, reviewed PRs only
- `feature/gaurav-backend`: backend and database improvements
- `feature/ichcha-ai`: AI, NLP, scoring, and explainability
- `feature/bk-frontend`: dashboard, tests, and documentation

### Commit conventions
- Use Conventional Commits:
  - `feat: add complaint analysis endpoint`
  - `fix: correct score normalization`
  - `docs: update README and contributing guide`
  - `test: add pipeline coverage tests`

### Pull requests
- Open one PR per feature branch
- Require at least one review from another team member
- Use squash merge into `main` for a clean history

## Testing
Run the test suite with:

```bash
python test_api.py
```

## Notes for reviewers
- Keep `main` stable and merge only completed feature work
- Make all documentation changes in `README.md` and `CONTRIBUTING.md`
- Track team ownership via branch names and issue assignments

## Project goals for evaluation
- Frequent, meaningful commits from all three team members
- Clear branch ownership and PR-based collaboration
- Strong documentation and setup guidance
- Clean, professional main branch history
