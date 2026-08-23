# 📦 ParcelPilot AI — Dual-Context Logistics Support & Operations Copilot

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![ChromaDB](https://img.shields.io/badge/Vector_DB-ChromaDB-purple.svg)](https://www.trychroma.com)
[![Groq / Gemini](https://img.shields.io/badge/LLM_Provider-Groq%20%7C%20Gemini-orange.svg)](https://groq.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**ParcelPilot AI** is an enterprise-grade, deterministic, and RBAC-enforced AI operations platform designed for complex logistics workflows. It provides grounded intelligence across customer self-service and internal support desks, resolving shipment inquiries, calculating contract-governed financial credits, diagnosing platform defects, and safely orchestrating business mutations.

---

## 🌟 Key Architecture & Capabilities

### 1. 👥 True Persona Separation & Dual System Prompts
- **Customer Self-Service Portal**: Direct 2nd-person communication (`"you"`, `"your shipment"`, `"your contract"`) with strict tenant isolation. Self-serve order tracking, fee calculation, and cancellation/RTO workflows.
- **Internal Operations Console**: Multi-tenant diagnostic workspace for Tier 1/2 Support Agents, CSMs, and Operations Managers. Includes cross-account ticket triage, SLA breach evaluations against the temporal snapshot (`2026-08-16 11:00 IST`), defect root-cause analysis (`KI-208`, `KI-211`), and escalation routing.

### 2. ⚖️ Precedence-Ranked Policy & Contract Engine
Evaluates conflicting documentation using a strict, mathematical source hierarchy:
$$\text{Signed Customer Agreements (Weight 100)} > \text{SOP v4 (80)} > \text{Policy v3 (70)} > \text{Product Guide (60)} > \text{Historical Tickets (0)}$$
- **Contract Overrides**: Automatically applies Northstar Clause 2 (100% cancellation fee waiver) and LumenWorks Clause 4 (2-hour delay threshold for 10% service credit) over general SOPs.
- **Obsolete Policy Isolation**: Explicitly excludes deprecated documents (e.g. Support Policy v2).
- **Historical Note Refutation**: Treats past human resolution notes (e.g. `TKT-451`) strictly as context, refuting erroneous agent claims using active engineering known issues.

### 3. 🛡️ Two-Phase State Mutation Protocol (Human-in-the-Loop)
The LLM is strictly prohibited from directly modifying the database. All state changes enforce a cryptographic 2-phase lifecycle:
1. **`prepare_action`**: Validates RBAC permissions, calculates financial impact, and creates a temporary proposal token (`act_...`) with a 15-minute TTL.
2. **`confirm_action`**: Mutations execute **only** when the user explicitly clicks **[Confirm]** or submits a verified confirmation payload.

### 4. 🧠 Multi-Turn Context Memory & Deterministic Calculations
- Multi-turn conversation retention across sessions (follow-ups like *"yes please cancel it"* resolve `ORD-1001` seamlessly).
- Zero-hallucination deterministic math for cancellation fees, service credits, and SLA breach timelines.
- Dual-provider LLM support (**Groq** `openai/gpt-oss-120b` / `llama-3.3-70b` & **Gemini** `gemini-3.7-flash` / `gemini-2.5-flash`) with an internal grounded fallback engine ensuring **100% uptime**.

---

## 🏗️ System Architecture

```mermaid
graph TD
    User([User / Browser UI]) -->|HTTP REST / SSE| API[FastAPI Application]
    API --> Middleware[RBAC & Auth Context Resolver]
    
    subgraph Reasoning & Orchestration Layer
        Middleware --> Orch[Agent Orchestrator]
        Orch --> DynamicPrompt[Dynamic Persona Prompt Builder]
        Orch --> LLM{LLM Provider Router}
        LLM -->|Primary| Groq[Groq API: openai/gpt-oss-120b]
        LLM -->|Fallback 1| Gemini[Google Gemini: gemini-3.7-flash]
        LLM -->|Fallback 2| DetEngine[Grounded Deterministic Reasoner]
    end

    subgraph Tools & Data Grounding Layer
        Orch --> RAG[Precedence-Ranked Vector Retriever]
        Orch --> QueryTools[SQL / ORM Query Tools]
        Orch --> CalcTools[Deterministic Calculation Engine]
        Orch --> ActionEngine[Two-Phase State Machine & TTL Store]
    end

    RAG --> ChromaDB[(ChromaDB Embeddings)]
    QueryTools --> DB[(SQLite Database: Orders, Tickets, Agreements)]
    ActionEngine --> DB
```

---

## 📁 Repository Structure

```text
ParcelPilot_Chatbot/
├── backend/
│   ├── agent/
│   │   ├── orchestrator.py        # Multi-turn reasoning loop & tool dispatch
│   │   ├── prompts.py             # Persona-specialized system prompts
│   │   └── tool_registry.py       # Central tool registry & schemas
│   ├── api/
│   │   └── main.py                # FastAPI REST endpoints & RBAC security
│   ├── db/
│   │   ├── database.py            # SQLAlchemy engine & session management
│   │   ├── models.py              # Account, Order, Ticket, and Action ORM models
│   │   └── seed.py                # Database seeder from assessment dataset
│   ├── rag/
│   │   ├── indexer.py             # PDF chunker, metadata tagger & ChromaDB indexer
│   │   └── retriever.py           # Precedence re-ranking & account scoping
│   ├── tools/
│   │   ├── action_engine.py       # Two-phase action state machine & TTL tokens
│   │   ├── calculation_tools.py   # Deterministic fee, credit & SLA calculators
│   │   └── query_tools.py         # Multi-tenant SQL lookup & masking tools
│   └── security.py                # RBAC roles, tenant validation & redaction
├── docs/
│   ├── requirements.md            # System requirements specification
│   ├── acceptance-criteria.md     # 9 evaluation categories & validation criteria
│   ├── data-dictionary.md         # Database schema & entity relationships
│   ├── deployment-guide.md        # Cloud deployment & live link guide
│   ├── future-roadmap-and-vision.md # Product roadmap & trade-off analysis
│   └── security-threat-model.md   # Adversarial threat model & defense layers
├── frontend/
│   ├── index.html                 # Responsive dashboard UI & action cards
│   ├── style.css                  # Modern dark-mode styling & telemetry badges
│   └── app.js                     # Persona switcher & multi-turn chat client
├── tests/
│   ├── test_rbac.py               # Tenant isolation & security unit tests
│   ├── test_calculations.py       # Deterministic business math unit tests
│   ├── test_rag.py                # Precedence retrieval & deprecation exclusion
│   ├── test_action_engine.py      # Two-phase mutation & TTL token tests
│   └── test_e2e_full_suite.py     # 44-test end-to-end evaluation suite
├── Dockerfile                     # Production container specification
├── requirements.txt               # Python package dependencies
├── run_server.py                  # Self-healing server launcher & port prober
└── README.md                      # Project documentation
```

---

## ⚡ Quickstart Guide (Local Setup)

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/ParcelPilot-AI.git
cd ParcelPilot-AI
```

### 2. Create and Activate a Virtual Environment
```bash
# On Windows
python -m venv venv
.\venv\Scripts\activate

# On macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```env
# Active LLM Provider: 'groq' or 'gemini'
LLM_PROVIDER=groq

# Groq Configuration (Recommended)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b

# Google Gemini Configuration (Fallback)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.7-flash

# Server Configuration
HOST=127.0.0.1
PORT=8000
```

### 5. Seed the Database & Build Vector Index
```bash
# Populate database tables with assessment data
python -m backend.db.seed

# Ingest and index corporate PDFs into ChromaDB
python backend/rag/indexer.py
```

### 6. Launch the Application
```bash
python run_server.py
```
Open your browser and navigate to **`http://127.0.0.1:8000`** (or the port indicated in the terminal).

---

## 🧪 Running the Test Suite

ParcelPilot AI includes an exhaustive test suite covering all 9 assessment categories, RBAC enforcement, deterministic math, and two-phase mutations:

```bash
# Run all unit and E2E assessment tests
python -m unittest discover -s tests -p "test_*.py"
```

---

## 🚀 Live Cloud Deployment & Shareable Links

ParcelPilot AI is ready for 1-click cloud deployment. See [`docs/deployment-guide.md`](docs/deployment-guide.md) for full instructions:
- **Free Cloud Web Service**: [Render.com](https://render.com) (`https://parcelpilot-ai.onrender.com`)
- **Instant Local Tunnel**: `cloudflared tunnel --url http://localhost:8000` or `npx localtunnel --port 8000`
- **Free Cloud Container**: [Koyeb.com](https://koyeb.com) (`https://parcelpilot-ai.koyeb.app`)
- **Hugging Face Free Tier**: [Hugging Face Spaces](https://huggingface.co/spaces) (Gradio SDK / 16GB RAM)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
