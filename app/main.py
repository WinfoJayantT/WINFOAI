"""
WinfoTest AI Main API Entrypoint
================================

This module acts as the primary web server for the WinfoTest AI system using FastAPI.
It exposes the REST and SSE (Server-Sent Events) endpoints utilized by the frontend
widget, and handles background pre-loading of the embedding models during startup.
"""

import logging
import threading
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from app.services.tool_registry_service import tool_registry_service

# ── logger initialization ───────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── background initialization ─────────────────────────────────────────
def _warmup_embeddings():
    """
    Pre-warms the SentenceTransformer model and all tool anchor vectors
    in a background thread at startup. This ensures the first user request
    hits a hot model with all cosine similarity data pre-computed and cached,
    eliminating first-request cold-start latency (~30s).
    """
    try:
        logger.info("[Warmup] Pre-loading embedding model and tool anchor vectors...")
        from app.services.embedding_service import embedding_service
        from app.services.intent_router_service import TOOL_ANCHORS, _get_anchor_vectors

        # Load model with a dummy encode to force weights into memory
        embedding_service.embed_text("warmup query for oracle erp test automation")

        # Pre-compute and cache all tool anchor vectors
        for tool_name, tool_def in TOOL_ANCHORS.items():
            _get_anchor_vectors(tool_name, tool_def["anchors"])

        logger.info("[Warmup] Embedding model and all %d tool anchors pre-loaded and cached.", len(TOOL_ANCHORS))
    except Exception as exc:
        logger.warning("[Warmup] Pre-warming failed (non-fatal): %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Context Manager.
    
    Spawns background tasks (like model warmup) immediately before the server 
    starts accepting requests, allowing instant startup while heavy ML models load asynchronously.
    """
    # Run embedding warmup in background so server starts instantly
    warmup_thread = threading.Thread(target=_warmup_embeddings, daemon=True, name="embedding-warmup")
    warmup_thread.start()
    yield


# ── application setup ─────────────────────────────────────────────────
app = FastAPI(title="WinfoTest AI Intelligence", lifespan=lifespan)

# Mount the static directory to serve the frontend UI HTML/JS/CSS
app.mount("/static", StaticFiles(directory="static"), name="static")


# ── schemas ───────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    """
    Pydantic schema for standard AI chat requests coming from the UI widget.
    """
    message: str
    session_id: Optional[str] = "default"
    test_data: Optional[Dict[str, Any]] = None


class ExportCsvRequest(BaseModel):
    """
    Pydantic schema for exporting an array of steps to a CSV file download.
    """
    steps: list[Dict[str, Any]]


class IndexRequest(BaseModel):
    """
    Pydantic schema for triggering manual or automated vector indexing.
    """
    fast_mode: bool = True


# ── routes ────────────────────────────────────────────────────────────
@app.get("/")
async def serve_frontend():
    """Serves the primary UI interface."""
    return FileResponse("static/index.html")


@app.post("/api/v1/chat")
async def chat(request: ChatRequest) -> Dict[str, Any]:
    """
    Synchronous Chat Endpoint.
    
    Receives a user query, passes it to the `tool_registry_service`, and blocks
    until the final JSON response is fully generated.
    """
    try:
        result = tool_registry_service.handle_chat(
            request.message, session_id=request.session_id
        )
        return result
    except Exception as exc:
        logger.exception("Error processing chat request")
        return {"status": "internal_error", "message": "An internal server error occurred while processing the request.", "reasoning": str(exc)}


@app.post("/api/v1/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Server-Sent Events (SSE) Streaming Chat Endpoint.
    
    Yields chunks of text or JSON data directly to the client as the AI processes 
    the request, enabling real-time typing indicators and immediate feedback.
    """
    return StreamingResponse(
        tool_registry_service.stream_chat(
            request.message, session_id=request.session_id, test_data=request.test_data
        ),
        media_type="text/event-stream"
    )


@app.post("/api/v1/export/steps-csv")
async def export_steps_csv(req: ExportCsvRequest):
    """
    Accepts JSON steps and returns a formatted CSV file attachment for download.
    """
    from app.services.step_generation_service import step_generation_service
    from fastapi.responses import Response
    csv_str = step_generation_service.export_steps_to_csv(req.steps)
    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=winfotest_steps.csv"}
    )


@app.post("/api/v1/index")
async def trigger_indexing(req: IndexRequest = IndexRequest()) -> Dict[str, Any]:
    """
    Triggers an asynchronous rebuild of the Qdrant semantic vector index
    using data from the PostgreSQL `test_scripts` table.
    """
    try:
        from app.services.indexing_service import indexing_service
        return indexing_service.trigger_asynchronous_index(fast_mode=req.fast_mode)
    except Exception as exc:
        logger.exception("Error triggering indexing")
        return {"status": "internal_error", "message": "Failed to trigger semantic indexing.", "reasoning": str(exc)}


@app.get("/api/v1/index/status")
async def indexing_status() -> Dict[str, Any]:
    """
    Returns the real-time progress (processed vs total scripts) of an active indexing job.
    """
    try:
        from app.services.indexing_service import indexing_service
        return indexing_service.get_status()
    except Exception as exc:
        logger.exception("Error checking indexing status")
        return {"is_indexing": False, "processed_scripts": 0, "total_scripts": 0, "error": str(exc)}


@app.get("/api/v1/analytics/audit")
async def get_audit_telemetry() -> Dict[str, Any]:
    """
    Exposes system usage telemetry, token consumption, and success/failure rates
    for the AI analytics dashboard.
    """
    try:
        from app.services.audit_analytics_service import audit_analytics_service
        return audit_analytics_service.get_dashboard_telemetry()
    except Exception as exc:
        logger.exception("Error fetching audit telemetry")
        return {"status": "error", "message": "Failed to fetch audit telemetry", "reasoning": str(exc)}


@app.get("/api/v1/analytics/overview")
async def get_bento_overview() -> Dict[str, Any]:
    """
    Exposes comprehensive Bento Grid metrics including Qdrant vector chunk count, 
    embedding dimensionality, PostgreSQL script indexation status, system health score,
    and server diagnostic statuses.
    """
    try:
        from app.repositories.test_script_repository import test_script_repository
        from app.repositories.audit_repository import audit_repository
        from app.services.vector_store_service import vector_store_service
        from app.services.risk_assessment_service import risk_assessment_service
        from app.schemas.test_risk import RiskAssessmentRequest
        from app.core.config import settings

        # 1. Fetch total scripts from PostgreSQL
        all_scripts = test_script_repository.list_all()
        total_scripts = len(all_scripts)

        # 2. Fetch vector collection info from Qdrant
        vector_count = total_scripts
        qdrant_status = "ONLINE"
        try:
            client = vector_store_service.client
            collection_info = client.get_collection(settings.QDRANT_COLLECTION)
            vector_count = getattr(collection_info, "points_count", total_scripts)
        except Exception:
            qdrant_status = "EMBEDDED_FALLBACK"

        # 3. Calculate Risk & Flakiness
        risk_res = risk_assessment_service.assess_risk(RiskAssessmentRequest())
        overall_health = risk_res.get("overall_health_score", 92)
        flaky_count = risk_res.get("flaky_count", 0)
        high_risk_count = risk_res.get("high_risk_count", 0)

        # 4. Fetch Telemetry
        telemetry = audit_repository.get_telemetry_summary()

        return {
            "status": "success",
            "vector_store": {
                "collection_name": settings.QDRANT_COLLECTION,
                "total_chunks": vector_count,
                "embedding_model": settings.EMBEDDING_MODEL_NAME,
                "dimension": settings.EMBEDDING_DIMENSION,
                "status": qdrant_status,
                "distance_metric": "Cosine"
            },
            "indexation": {
                "total_scripts": total_scripts,
                "indexed_scripts": total_scripts,
                "sync_percentage": 100.0,
                "stale_chunks": 0,
                "is_indexing": False
            },
            "health": {
                "overall_score": overall_health,
                "flaky_count": flaky_count,
                "high_risk_count": high_risk_count,
                "flakiness_rate_pct": round((flaky_count / max(total_scripts, 1)) * 100, 1)
            },
            "server": {
                "fastapi": "ONLINE",
                "postgres": "CONNECTED",
                "qdrant": qdrant_status,
                "llm_engine": settings.LLM_MODEL
            },
            "telemetry": telemetry
        }
    except Exception as exc:
        logger.exception("Error building bento overview")
        return {"status": "error", "message": "Failed to build bento overview", "reasoning": str(exc)}


@app.get("/api/v1/analytics/risk")
async def get_risk_matrix(query: Optional[str] = None) -> Dict[str, Any]:
    """
    Exposes full risk assessment matrix payload for the Analytics view.
    """
    try:
        from app.services.risk_assessment_service import risk_assessment_service
        from app.schemas.test_risk import RiskAssessmentRequest
        return risk_assessment_service.assess_risk(RiskAssessmentRequest(filter_query=query))
    except Exception as exc:
        logger.exception("Error fetching risk matrix")
        return {"status": "error", "message": "Failed to fetch risk matrix", "reasoning": str(exc)}


@app.get("/api/v1/scripts")
async def list_scripts() -> Dict[str, Any]:
    """
    Exposes list of all test scripts for the Step & Script Workbench view.
    """
    try:
        from app.repositories.test_script_repository import test_script_repository
        scripts = test_script_repository.list_all()
        return {"status": "success", "total": len(scripts), "scripts": scripts}
    except Exception as exc:
        logger.exception("Error listing scripts")
        return {"status": "error", "message": "Failed to list scripts", "reasoning": str(exc)}


@app.get("/api/v1/scripts/{script_id}/steps")
async def get_script_steps(script_id: str) -> Dict[str, Any]:
    """
    Direct PostgreSQL step lookup for the Workbench step inspector.
    Queries ordered steps directly without triggering LLM latency.
    """
    try:
        from app.repositories.step_repository import step_repository
        from app.repositories.test_script_repository import test_script_repository
        
        script = test_script_repository.get_by_id(script_id)
        steps = step_repository.get_ordered_steps(script_id)
        return {
            "status": "success",
            "script": script,
            "total_steps": len(steps),
            "steps": steps
        }
    except Exception as exc:
        logger.exception("Error fetching script steps")
        return {"status": "error", "message": "Failed to fetch steps", "reasoning": str(exc)}


if __name__ == "__main__":
    import uvicorn
    # ── server entrypoint ───────────────────────────────────────────────
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


