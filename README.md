# WinfoTest AI Core Backend

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Architecture](https://img.shields.io/badge/architecture-FastAPI%20%7C%20Qdrant%20%7C%20Postgres-lightgrey)
![Guardrails](https://img.shields.io/badge/AST%20Scanner-Enabled-orange)

This repository contains the backend service for the WinfoTest AI system. It provides an LLM-driven intent routing architecture over a local vector store and PostgreSQL database, enforcing strict repository-pattern data access for enterprise ERP QA Automation.

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Core Engineering Guardrails](#core-engineering-guardrails)
3. [Prerequisites & Requirements](#prerequisites--requirements)
4. [Local Setup & Deployment](#local-setup--deployment)
5. [Internal API Reference](#internal-api-reference)
6. [Monitoring & Observability](#monitoring--observability)
7. [Troubleshooting & Runbooks](#troubleshooting--runbooks)
8. [Development Workflow & CI/CD](#development-workflow--cicd)

---

## System Architecture

The AI backend is designed around a strictly decoupled tool-registry pattern. The LLM acts purely as a router and reasoning engine, while data hydration is strictly handled by standard RDBMS queries.

```mermaid
graph TD
    Client[Client UI / API] -->|HTTP POST| FastAPI[FastAPI Server]
    FastAPI --> IntentRouter[LLM Intent Router]
    
    IntentRouter <-->|Prompt & Schema| LLM[Ollama / OpenAI]
    IntentRouter -->|Validated Args| ToolRegistry[Tool Registry Service]
    
    ToolRegistry --> VectorDB[(Qdrant Vector DB)]
    ToolRegistry --> RepoLayer[app/repositories]
    
    VectorDB -.->|Returns IDs only| RepoLayer
    RepoLayer <--> Postgres[(PostgreSQL Source of Truth)]
```

### Architecture Stack

| Component | Technology | Implementation Details |
| :--- | :--- | :--- |
| **API Framework** | FastAPI | Asynchronous REST server routing AI and indexing requests. |
| **LLM Inference** | Ollama / OpenAI | Handles intent classification, query rewriting, and document synthesis. |
| **Embedding Engine** | `sentence-transformers` | Runs `all-mpnet-base-v2` locally (CPU). Outputs 768-dimensional dense vectors. |
| **Vector Store** | Qdrant | In-memory/On-disk vector index running on `localhost:6333`. |
| **RDBMS** | PostgreSQL | Runs on `localhost:5432`. All final entities are hydrated from here. |
| **ORM** | SQLAlchemy | Synchronous/Asynchronous DB connection pool managing schema state. |

---

## Core Engineering Guardrails

This project enforces strict isolation between LLM reasoning and system execution. **Violating these guardrails in pull requests will result in immediate rejection.**

1. **Absolute Source of Truth:** The vector database (Qdrant) is strictly an index. Services *must* reload all entities (scripts, users, processes) directly from PostgreSQL before returning payloads. **Never return raw vector metadata as the final response.**
2. **Strict Repository Isolation:** Direct SQL queries or ORM calls are restricted exclusively to `app/repositories/*.py`. Routers, tools, and services must never query the database directly.
3. **No Hardcoded Logic or Silent Fallbacks:** 
    - Keyword-based routing (e.g., `if "invoice" in query`) is banned. 
    - Hardcoded canonical schemas (`CANONICAL_ERP_SCHEMAS`) are banned.
    - If data is ambiguous or missing, the system must return a structured error status (e.g., `not_found`, `ambiguous`). Mock data generation is prohibited.
4. **Tool Registry Pattern:** LLM requests must map to a registered tool in `tool_registry_service.py`. All inputs and outputs must pass through Pydantic schema validation (`app/schemas/`).

---

## Prerequisites & Requirements

- **OS:** Linux (Ubuntu 22.04+) or Windows with WSL2.
- **Python:** System Python `3.10` or higher.
- **RAM:** Minimum 8GB (Requires ~2GB dedicated to loading `all-mpnet-base-v2` into memory).
- **Dependencies:** `docker` and `docker-compose` for infrastructure.

---

## Local Setup & Deployment

*Note: This environment is configured to run directly on the system Python installation. No virtual environment is required.*

### 1. Start Infrastructure Dependencies
PostgreSQL and Qdrant must be running locally.

```bash
docker-compose up -d
docker ps | findstr "5432 6333" # Verify ports on Windows
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory.

```env
# Server
ENV=local
LOG_LEVEL=DEBUG

# Relational Database
DATABASE_URL=postgresql+psycopg2://winfotest:winfotest@localhost:5432/winfotest
DATABASE_SCHEMA=public

# Vector Index
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=winfotest_semantic_scripts

# Local ML Models
EMBEDDING_MODEL_NAME=all-mpnet-base-v2
EMBEDDING_DIMENSION=768

# LLM Inference API
OPENAI_API_KEY=sk-...
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5-coder:7b
OLLAMA_BASE_URL=http://localhost:11434/v1
LLM_TIMEOUT_SECONDS=120.0
```

### 4. Initialize Database Schema
If this is a fresh setup, execute the initialization SQL script to provision the public schema.

```bash
psql -h localhost -U winfotest -d winfotest -f sql/init_db.sql
```

### 5. Run the API Server
Start the FastAPI application.

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Internal API Reference

### POST `/api/v1/index`
Trigger asynchronous embedding generation and Qdrant indexing for database records.

**Payload:**
```json
{
  "fast_mode": true
}
```

### POST `/api/v1/chat`
Main entrypoint for the LLM intent router. Evaluates the message, rewrites using conversation history, and dispatches to a Pydantic-validated tool.

**Payload:**
```json
{
  "message": "Execute the AP invoice test script",
  "session_id": "debug_session_01"
}
```

---

## Monitoring & Observability

- **Application Logs:** Configured via `LOG_LEVEL` in `.env`. Structured JSON logging should be enabled in production environments for Datadog/ELK ingestion.
- **Trace Output:** Every tool execution returns a structured `debug_trace` object containing execution time, detected intent, tool selection, parsed arguments, and repository execution paths.

---

## Troubleshooting & Runbooks

| Symptom | Probable Cause | Resolution |
| :--- | :--- | :--- |
| **Qdrant Connection Refused** | Container not running or port conflict. | `docker restart qdrant` and ensure port `6333` is free. |
| **OOM Killed on Indexing** | `sentence-transformers` exhausted system RAM. | Reduce batch size in indexing service or increase host RAM limits. |
| **LLM Timeout Errors** | Local Ollama instance is overloaded. | Check `OLLAMA_BASE_URL` health. Increase `LLM_TIMEOUT_SECONDS`. |
| **Database Lock / Hung Query** | Unclosed SQLAlchemy sessions. | Check repository layer for missing `try/finally` session teardowns. |

---

## Development Workflow & CI/CD

The project includes an AST scanner to enforce architectural rules statically. **This is enforced in the CI pipeline.**

```bash
python scripts/check_guardrails.py
```

This script parses Python ASTs and regex patterns to ensure:
- No `session.execute` or `db.query` calls exist outside of `app/repositories/`.
- Banned dictionary structures (like `CANONICAL_ERP_SCHEMAS`) are not present.
- Vector search functions do not bypass the PostgreSQL rehydration step.
