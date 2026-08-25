import logging
from typing import Any

from app.core.config import settings
from app.repositories.audit_repository import audit_repository
from app.services.indexing_service import indexing_service

logger = logging.getLogger(__name__)


class AuditAnalyticsService:
    """Provides aggregated enterprise telemetry, audit trail reporting, and vector index health metrics."""

    def get_dashboard_telemetry(self) -> dict[str, Any]:
        try:
            telemetry = audit_repository.get_telemetry_summary()
            recent_logs = audit_repository.get_recent_logs(limit=15)
            index_status = indexing_service.get_status()

            qdrant_info = {
                "collection_name": settings.QDRANT_COLLECTION,
                "embedding_model": settings.EMBEDDING_MODEL_NAME,
                "dimension": settings.EMBEDDING_DIMENSION,
                "is_indexing": index_status.get("is_indexing", False),
                "indexed_scripts": index_status.get("processed_scripts", 0),
                "total_scripts": index_status.get("total_scripts", 0),
            }

            return {
                "status": "success",
                "telemetry": telemetry,
                "recent_audit_logs": recent_logs,
                "vector_index_health": qdrant_info,
                "database_schema": settings.DATABASE_SCHEMA,
                "llm_model": settings.LLM_MODEL,
                "environment": settings.ENV,
            }
        except Exception as exc:
            logger.error(f"Error compiling audit dashboard telemetry: {exc}")
            return {
                "status": "error",
                "message": "Failed to compile enterprise telemetry.",
                "reasoning": str(exc),
            }


audit_analytics_service = AuditAnalyticsService()
