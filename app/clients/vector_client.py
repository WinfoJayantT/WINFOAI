"""
Owns the raw QdrantClient connection. vector_store_service.py builds on top of
this. Section 25: production must use a persistent store; only ENV=local /
ENV=test may fall back to an on-disk or in-memory client.
"""

import logging

from qdrant_client import QdrantClient

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorClient:
    def __init__(self) -> None:
        self.client = self._build_client()

    def _build_client(self) -> QdrantClient:
        if settings.QDRANT_URL:
            logger.info("Connecting to Qdrant at %s", settings.QDRANT_URL)
            return QdrantClient(url=settings.QDRANT_URL)

        if settings.ENV == "production":
            raise RuntimeError(
                "QDRANT_URL is required in production (PROJECT_CONTEXT_FINAL.md section 25: "
                "no silent in-memory fallback)."
            )

        logger.warning("QDRANT_URL not set; falling back to on-disk Qdrant (ENV=%s only).", settings.ENV)
        return QdrantClient(path="data/qdrant_storage")


vector_client = VectorClient()
