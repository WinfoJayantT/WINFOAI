# WinfoTest AI Assistant - System Rules & Engineering Guardrails

## 1. Absolute Source of Truth Rule
- All production data MUST originate from the WinfoTest PostgreSQL database.
- Vector database (Qdrant) is strictly an INDEX, not a source of truth. Final responses must reload entities from PostgreSQL.
- NEVER produce responses from vector payloads alone.

## 2. Architectural Boundaries
- **Repository Isolation:** Direct database or SQLAlchemy queries are strictly restricted to `app/repositories/*.py`.
- Service files MUST call repositories. Services, tools, clients, or routers must NEVER execute raw SQL or ORM queries directly.

## 3. Tool Registry & Schema Validation
- The LLM must NEVER execute arbitrary code or query the database directly.
- Every LLM request must be mapped to a registered tool in `tool_registry_service.py`.
- Every tool call MUST validate inputs and outputs using Pydantic schemas defined in `app/schemas/`. Do NOT trust raw dicts.

## 4. No Hardcoded Business Logic & No Silent Fallbacks
- **Banned Patterns:** Keyword-based routing (e.g., `if "supplier" in query`), static canonical ERP schemas (`CANONICAL_ERP_SCHEMAS`), or canonical steps.
- **Strict Error Handling:** If a entity (user, script, process) is missing or ambiguous, return structured status (`not_found`, `ambiguous`, `insufficient_data`). NEVER silently fall back to generic data or mock fallback data in production code.

## 5. Debug Traces
- Every tool execution MUST build and return a structured `debug_trace` containing execution time, detected intent, selected tool, parsed arguments, repository methods executed, and warnings.

## 6. Execution Authority
- Do NOT directly run Playwright or duplicate WinfoTest execution logic. Future test runs must go through `WinfoTestExecutionClient`.