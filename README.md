# PriorityPulse-AI: SRE-Aligned Complaint Intelligence Engine

## 🚀 Overview
**PriorityPulse-AI** is a production-grade incident intelligence system designed to move beyond traditional keyword-based customer support. It transforms raw customer complaints into actionable, prioritized technical insights by combining **Deterministic SRE Metrics** with **Probabilistic LLM Reasoning**.

Unlike standard NLP systems, PriorityPulse-AI focuses strictly on **Systemic Risk** and **Business Impact**, removing customer-identity bias and focusing on keep-the-lights-on operations.

---

## 🧠 The I.U.S.M. Scoring Framework
The core of the system is the hybrid **I.U.S.M.** framework, which balances hard system data with nuanced language understanding.

### 🔴 Deterministic Layer (The "Eyes" of the System)
These factors are calculated locally using **Vector Similarity (Sentence-Transformers)** and **Time-Decay Algorithms**.

*   **S - Systemic Risk (Mass Incidence)**: 
    * *Formula*: `Σ (sim_i * e^(-0.1 * hours_ago))`
    * Detects semantic clusters of similar complaints across the fleet. It Uses an exponential time-decay to prioritize sudden "spikes" in specific problems over historical noise.
*   **M - Incident Match (Outage Correlation)**: 
    * Cross-references every incoming complaint against a live (or mock) list of known **Active System Incidents** (e.g., "Stripe API Down"). Values are slammed to zero if similarity falls below a strict 0.55 confidence threshold to prevent false positives.

### 🟣 Probabilistic Layer (The "Brain" of the System)
These factors are extracted via **Llama-3.1-8b (via Groq)** or **GPT-4** using strict SRE constraints.

*   **U - Urgency**: Analyzes user language for signals of immediate failure, blockages, or emergency status.
*   **I - Impact (Blast Radius)**: Assesses the criticality of the affected feature (e.g., Payments have higher weight than UI color issues).

### ⚖️ The Weighted Formula
```python
Final_Score = (0.35 * S) + (0.15 * M) + (0.25 * U) + (0.25 * I)
```
*   **75 - 100**: CRITICAL (Auto-Escalate 🔥)
*   **55 - 74**: HIGH
*   **35 - 54**: MEDIUM
*   **00 - 34**: LOW

---

## 🛠️ Architecture & Workflow

1.  **Ingestion**: Complaint enters via FastAPI.
2.  **Preprocessing**: Text is cleaned and entities (Product version, OS, UUIDs) are extracted via **spaCy**.
3.  **Vectorization**: The text is converted into a 384-dimensional embedding.
4.  **Deterministic Engine**: 
    *   Searches SQLite for semantic neighbors (Systemic Risk).
    *   Compares against active outages (Incident Match).
5.  **LLM Inference (Groq)**: The LLM receives the text + the deterministic scores. It performs a "Chain-of-Thought" analysis to determine Urgency and Impact.
6.  **Scoring**: The Hybrid Formula calculates the final score.
7.  **Visualization**: Results are served to a high-performance dashboard with full transparency into the "Reasoning" behind the score.

---

## 📂 Project Structure
```text
PriorityPulse-AI/
├── app/
│   ├── api/
│   │   └── routes.py         # FastAPI Endpoints (Complaints, Analyse, Dashboard)
│   ├── db/
│   │   └── database.py       # SQLAlchemy Session Management
│   ├── models/
│   │   ├── complaint.py      # Core Complaint Schema (incl. Contextual Fields)
│   │   └── priority.py       # Scoring Metrics & LLM Reasoning Storage
│   ├── schemas/
│   │   ├── request.py        # Pydantic Input Validation
│   │   └── response.py       # Unified API Response Models
│   ├── services/
│   │   ├── nlp.py            # Vector similarity, S & M calculations
│   │   ├── llm_engine.py     # Groq/OpenAI Integration & SRE Constraints
│   │   └── scoring.py        # Hybrid Weighted Formula & Escalation Logic
│   └── main.py               # Application Entrypoint
├── tests/
│   └── test_api.py           # End-to-end API Simulation Script
├── dashboard.html            # Premium SRE Monitoring Dashboard
├── .env                      # API Keys & Secrets
├── requirements.txt          # Pinned Dependencies
├── data/
│   └── complaints.db         # Local SQLite Database (Generated on first run)
└── docs/                     # Extended technical documentation and diagrams
```

---

## ⚡ Setup & Installation

### 1. Environment Setup
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# OR
.\venv\Scripts\activate   # Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_key_here
# Optional: OPENAI_API_KEY=your_key_here
```

### 4. Run the System
```bash
# Start the FastAPI Server
uvicorn app.main:app --reload

# Run a Test Simulation
python tests/test_api.py
```

---

## 📊 Dashboard Access
Open `dashboard.html` in your browser. It connects to `localhost:8000` to show real-time metrics, internal scores, and the "Chain-of-Thought" reasoning for every prioritized incident.
