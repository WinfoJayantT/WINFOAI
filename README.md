# WinfoTest AI Intelligence Engine

<div align="center">

![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-4169E1?logo=postgresql&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20DB-DC382D?logo=qdrant&logoColor=white)
![Ollama](https://img.shields.io/badge/Local%20LLM-Qwen%202.5-black?logo=ollama&logoColor=white)
![Architecture](https://img.shields.io/badge/Architecture-Hybrid%20RAG%20%7C%20Zero--Hardcoding-success)
![Performance](https://img.shields.io/badge/Performance-Enterprise%20Ready%20%7C%20Low%20Memory%20Mode-ff69b4)

**A PostgreSQL-grounded, enterprise autonomous AI test intelligence platform for Oracle Cloud ERP QA automation, featuring hybrid RAG semantic discovery, concurrent multi-intent execution, fast-mode indexing, and self-healing locator repair—optimized to run flawlessly even on low-spec developer laptops.**

[Features](#-key-capabilities) • [Architecture](#-system-architecture) • [UI Overview](#-enterprise-web-interface) • [Guardrails](#-engineering-guardrails) • [Quickstart](#-quickstart--installation) • [API Reference](#-api-reference) • [Testing](#-testing--quality-assurance)

</div>

---

## Executive Summary

Enterprise ERP testing across platforms like Oracle Fusion Cloud (Procure to Pay, Order to Cash, Record to Report, HCM, SCM) is notoriously complex. Test suites suffer from fragile UI dynamic locators, complex multi-stage business rules, lack of semantic searchability, and opaque test failures.

**WinfoTest AI** bridges this gap by acting as an autonomous intelligence and reasoning layer over PostgreSQL test metadata and Qdrant vector spaces. It operates under a **Zero-Hardcoding & 100% Dynamic Grounding Policy**, translating natural language business queries into verified database lookups, high-depth test script generation (15+ steps), automated failure root-cause analysis, and self-healing Playwright/Selenium locator repairs.

The platform is designed to be **Enterprise Ready**, featuring concurrent multi-intent query execution, blazing-fast vector indexing, and a **Low Memory / Fast Mode** that dynamically throttles CPU threads so the AI can run smoothly alongside local IDEs on any developer machine.

---

## Key Capabilities

### 1. Hybrid Intent Router (Dense Vector + Micro-Schema Extraction + Regex Fast-Paths)
* **Zero-Latency Regex Fast-Paths**: Bypasses LLM overhead entirely for highly structured lookups (e.g., exact script IDs) via regex extraction, returning intents in ~15ms.
* **Sub-Second Intent Resolution**: Uses a dense vector router (`nomic-embed-text`) with cosine similarity thresholding (0.70 confidence calibration) to identify tool intents.
* **Micro-LLM Dynamic Parsing**: Extracts strongly-typed Pydantic arguments using localized greedy decoding (`qwen2.5-coder:1.5b`) without slow conversational overhead.
* **Concurrent Multi-Intent Execution**: Executes complex multi-tool queries (e.g., "Run tests and cluster scripts") in parallel using `asyncio.gather()`, reducing total wait time to the speed of the slowest tool.

### 2. Semantic Discovery & Hybrid Search (Vector + Full-Text RAG)
* **Dense & Keyword Fusion**: Combines Qdrant dense vector search with PostgreSQL ILIKE/full-text keyword ranking.
* **PostgreSQL Entity Rehydration**: Vector searches return database UUIDs only; 100% of script entities, descriptions, and workflow steps are reloaded live from PostgreSQL to prevent stale AI hallucinations.

### 3. Dynamic High-Depth Step Synthesis (15+ Steps)
* **Realistic Enterprise Workflow Generation**: Synthesizes 15+ comprehensive ERP automation steps complete with action verbs, UI navigation breadcrumbs, input parameter binds, and validation assertions.
* **Zero Dummy Fallbacks**: Generates authentic business logic dynamically based on Oracle Cloud Modern Best Practice (MBP) taxonomies.

### 4. End-to-End Test Suite Chaining & Coverage Gap Analysis
* **Sequential Dependency Sorting**: Assembles multi-stage regression suites across complex enterprise flows (e.g. Requisition -> PO Approval -> Goods Receipt -> AP Invoice Matching -> Payment Hold -> GL Posting).
* **Process Gap Detection**: Flags missing validation gates and estimates total execution runtimes.

### 5. Enterprise Readiness & Performance Optimization
* **Low Memory / Fast Mode Toggle**: Includes a front-end toggle that throttles the backend execution engine. When enabled, multi-intent parallel tasks are bounded by a `ThreadPoolExecutor` to prevent CPU exhaustion on low-spec developer laptops.
* **Aggressive Code Optimization**: Validated through strict `ruff` static analysis, the architecture contains zero redundant bloat or unused variables, ensuring rapid sub-second startup times.

### 6. Root Cause Failure Analysis & Self-Healing Locator Repair
* **Automated Log Diagnosis**: Analyzes stack traces and Playwright `TimeoutError` logs to explain root causes and recommend actionable fixes.
* **Dynamic Locator Healing**: Extracts fragile auto-generated dynamic IDs (e.g. Oracle ADF dynamic container tags) directly from error logs and synthesizes resilient semantic XPath/ARIA selectors with calculated resilience scores.

### 7. Test Health, Risk Assessment & Flakiness Scoring
* **Live Telemetry Analytics**: Queries PostgreSQL execution logs to calculate failure rates, step flakiness, and stability scores across enterprise modules.

---

## System Architecture

The platform enforces a decoupled **Tool-Registry & Repository Pattern**, completely separating AI reasoning from database persistence. The ORM layer is fully self-contained within the AI repository (`app/winfo_test_orm`), completely decoupled from external ERP engineering repositories to guarantee robust containerized deployments.

```mermaid
graph TD
    User([Enterprise User / QA Engineer]) -->|SSE Stream / JSON| WebUI[Modern Glassmorphic Web UI]
    WebUI -->|HTTP POST /api/v1/chat/stream| FastAPI[FastAPI Gateway]
    
    subgraph "Reasoning & Intent Layer"
        FastAPI --> HybridRouter[Hybrid Intent Router]
        HybridRouter <-->|Vector Cosine Match| IntentAnchors[(Dense Vector Embeddings)]
        HybridRouter <-->|Regex / Fast-Path| FastMatch[Zero-Latency Matcher]
        HybridRouter <-->|Arg Extraction| LocalLLM[Local LLM - Qwen 2.5]
    end
    
    subgraph "Tool Dispatcher & Core Services"
        HybridRouter -->|Validated Pydantic Payload| ToolRegistry[Tool Registry Service]
        ToolRegistry -->|Concurrent Execution| StepGen[Step Generation Service]
        ToolRegistry -->|Concurrent Execution| SearchService[Semantic Search Service]
        ToolRegistry -->|Concurrent Execution| SuiteService[Test Suite Service]
        ToolRegistry --> FailureService[Failure Analysis & Self-Healing]
    end
    
    subgraph "Data & Persistence Layer"
        SearchService <-->|Dense Search| Qdrant[(Qdrant Vector DB)]
        StepGen & SearchService & SuiteService & FailureService -->|Live Entity Rehydration| RepoLayer[Repository Layer]
        RepoLayer <-->|app.winfo_test_orm| PostgreSQL[(PostgreSQL Source of Truth)]
    end
```

---

## Tech Stack

| Domain | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI | Asynchronous API gateway with Server-Sent Events (SSE) streaming |
| **Relational Database** | PostgreSQL 15+ | Single Source of Truth for test scripts, execution runs, steps, and audit logs |
| **Vector Database** | Qdrant | On-disk / In-memory vector store hosting 768-dim embeddings |
| **Embedding Engine** | `sentence-transformers` | Runs `nomic-embed-text` locally on CPU |
| **Local LLM Engine** | Ollama (`qwen2.5-coder`) | `qwen2.5-coder:1.5b` (Fast Router) & `7b` (Complex Synthesis) |
| **ORM & Data Access** | SQLAlchemy | Repository-pattern connection pool via self-contained `app/winfo_test_orm` |
| **Frontend UI** | Vanilla JS + Tailwind CSS | Responsive UI with CRT diagnostics, dark/light themes, and persistent sessions |

---

## Enterprise Web Interface

The frontend provides an enterprise developer experience designed for high-density QA telemetry:

* **Real-time SSE Streaming**: Instant token streaming for assistant responses alongside structured cards.
* **Persistent Session History**: Retains full conversational timeline across page refreshes via `localStorage` until explicitly reset.
* **Live Telemetry & Diagnostics**: Real-time connection monitoring, database grounding indicators, and tool routing analytics.
* **Dark / Light Theme Toggle**: Persistent aesthetic switching with optimized contrast ratios.
* **Zero Emojis & Distractions**: Clean, minimal corporate typography using Google Inter and Geist Mono fonts.

---

## Engineering Guardrails

To ensure reliability, this codebase enforces strict architectural constraints verified by static AST scanners (`scripts/check_guardrails.py`):

1. **Absolute PostgreSQL Source of Truth**: Qdrant stores only vector embeddings and script UUIDs. Services must rehydrate full records from PostgreSQL before returning responses.
2. **Strict Repository Pattern Isolation**: Direct SQL statements or ORM queries are restricted exclusively to `app/repositories/`. Routers, tools, and services never query the database directly.
3. **Zero Hardcoded Business Fallbacks**: Hardcoded script arrays, static locators, or mock data generation are strictly forbidden. If an entity is not found, the system returns an auditable `not_found` or `ambiguous` status.
4. **Pydantic Validation**: All tool arguments and outputs pass through strict Pydantic schemas (`app/schemas/`).

---

## Quickstart & Installation

### 1. Clone Repository
```bash
git clone https://github.com/WinfoJayantT/WINFOAI.git
cd WINFOAI
```

### 2. Start Infrastructure (PostgreSQL & Qdrant)
```bash
docker-compose up -d
```

### 3. Setup Python Environment & Dependencies
```bash
pip install -r requirements.txt
```

### 4. Pull Local LLMs (via Ollama)
Ensure Ollama is installed and running:
```bash
ollama pull qwen2.5-coder:1.5b
ollama pull qwen2.5-coder:7b
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env` and adjust database credentials:
```bash
cp .env.example .env
```

```env
ENV=local
LOG_LEVEL=INFO

# Relational Database
DATABASE_URL=postgresql+psycopg2://postgres:your_password@localhost:5432/postgres
DATABASE_SCHEMA=public

# Vector Store
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=winfotest_semantic_scripts

# Local ML Models
EMBEDDING_MODEL_NAME=all-mpnet-base-v2
EMBEDDING_DIMENSION=768

# LLM Inference
FAST_LLM_MODEL=qwen2.5-coder:1.5b
LLM_MODEL=qwen2.5-coder:7b
OLLAMA_BASE_URL=http://localhost:11434/v1
```

### 6. Run Database Initialization
```bash
python scripts/init_ai_tables.py
```

### 7. Launch the Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser and navigate to **`http://localhost:8000`**.

---

## API Reference

### 1. Streaming Chat Endpoint
* **URL**: `/api/v1/chat/stream`
* **Method**: `POST`
* **Content-Type**: `application/json` (Returns `text/event-stream`)

**Request Body:**
```json
{
  "message": "Generate automation steps for entering a matched supplier invoice with 2-way PO matching",
  "session_id": "default"
}
```

**Stream Events:**
* `data: {"type": "token", "content": "..."}` — Live conversational tokens.
* `data: {"type": "done", "results": [...]}` — Final structured JSON tool cards.

---

### 2. Semantic Document Indexing
* **URL**: `/api/v1/index`
* **Method**: `POST`

**Request Body:**
```json
{
  "fast_mode": true
}
```

* **URL**: `/api/v1/index/status`
* **Method**: `GET`
* **Response**:
```json
{
  "is_indexing": false,
  "processed_scripts": 44,
  "total_scripts": 44,
  "percentage": 100
}
```

---

## Testing & Quality Assurance

### Run Unit & Integration Tests
```bash
pytest tests/ -v
```

### Run Static AST Guardrail Checks
```bash
python scripts/check_guardrails.py
```

---

## Repository Structure

```
.
├── app/
│   ├── clients/             # LLM (Ollama), Vector (Qdrant), and Execution Clients
│   ├── core/                # Configuration settings and structured logging
│   ├── models/              # SQLAlchemy ORM database models
│   ├── repositories/        # Strict SQL persistence layer (Zero direct SQL in services)
│   ├── schemas/             # Pydantic schemas for intents, tools, and responses
│   ├── services/            # Core business logic (Router, Search, StepGen, Healing, Suite)
│   └── main.py              # FastAPI server entrypoint
├── config/                  # Oracle MBP business process taxonomies
├── data/                    # Qdrant vector storage mount
├── scripts/                 # Schema setup, indexing, and guardrail enforcement scripts
├── sql/                     # PostgreSQL initialization DDL
├── static/                  # Glassmorphic developer UI (index.html)
├── tests/                   # Pytest suite
├── docker-compose.yml       # PostgreSQL and Qdrant container definitions
├── requirements.txt         # Python package dependencies
└── README.md                # Enterprise system documentation
```

---

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.
