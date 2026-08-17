import logging
import threading
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from app.services.tool_registry_service import tool_registry_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

        # Load model with a dummy encode
        embedding_service.embed_text("warmup query for oracle erp test automation")

        # Pre-compute and cache all tool anchor vectors
        for tool_name, tool_def in TOOL_ANCHORS.items():
            _get_anchor_vectors(tool_name, tool_def["anchors"])

        logger.info("[Warmup] Embedding model and all %d tool anchors pre-loaded and cached.", len(TOOL_ANCHORS))
    except Exception as exc:
        logger.warning("[Warmup] Pre-warming failed (non-fatal): %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run embedding warmup in background so server starts instantly
    warmup_thread = threading.Thread(target=_warmup_embeddings, daemon=True, name="embedding-warmup")
    warmup_thread.start()
    yield


app = FastAPI(title="WinfoTest AI Intelligence", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"


@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")


@app.post("/api/v1/chat")
async def chat(request: ChatRequest) -> Dict[str, Any]:
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
    return StreamingResponse(
        tool_registry_service.stream_chat(request.message, session_id=request.session_id),
        media_type="text/event-stream"
    )

class IndexRequest(BaseModel):
    fast_mode: bool = True

@app.post("/api/v1/index")
async def trigger_indexing(req: IndexRequest = IndexRequest()) -> Dict[str, Any]:
    try:
        from app.services.indexing_service import indexing_service
        return indexing_service.trigger_asynchronous_index(fast_mode=req.fast_mode)
    except Exception as exc:
        logger.exception("Error triggering indexing")
        return {"status": "internal_error", "message": "Failed to trigger semantic indexing.", "reasoning": str(exc)}

@app.get("/api/v1/index/status")
async def indexing_status() -> Dict[str, Any]:
    try:
        from app.services.indexing_service import indexing_service
        return indexing_service.get_status()
    except Exception as exc:
        logger.exception("Error checking indexing status")
        return {"is_indexing": False, "processed_scripts": 0, "total_scripts": 0, "error": str(exc)}


@app.get("/api/v1/analytics/audit")
async def get_audit_telemetry() -> Dict[str, Any]:
    try:
        from app.services.audit_analytics_service import audit_analytics_service
        return audit_analytics_service.get_dashboard_telemetry()
    except Exception as exc:
        logger.exception("Error fetching audit telemetry")
        return {"status": "error", "message": "Failed to fetch audit telemetry", "reasoning": str(exc)}

