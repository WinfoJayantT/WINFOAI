import logging
import uuid
from typing import Any, List, Optional
from sqlalchemy import text
from app.core.config import settings
from app.repositories.db import engine

logger = logging.getLogger(__name__)


class IndexRepository:
    def __init__(self):
        self._ensure_ai_tables()

    def _ensure_ai_tables(self):
        """Ensures AI-owned tables exist in PostgreSQL per Section 29 guardrails."""
        try:
            with engine.connect() as conn:
                conn.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS ai_semantic_documents (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        test_script_id UUID NOT NULL,
                        semantic_document TEXT NOT NULL,
                        generated_by VARCHAR(50) DEFAULT 'llm',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """
                    )
                )
                conn.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS ai_vector_index_status (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        test_script_id UUID NOT NULL,
                        embedding_model VARCHAR(100) NOT NULL,
                        dimension INT NOT NULL,
                        indexed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """
                    )
                )
                conn.commit()
        except Exception as exc:
            logger.debug(
                "Could not auto-create AI tables (might already exist or lack DDL perms): %s",
                exc,
            )

    def record_semantic_document(
        self, script_id: str, document: str, generated_by: str = "llm"
    ):
        self._ensure_ai_tables()
        try:
            with engine.connect() as conn:
                conn.execute(
                    text(
                        """
                        INSERT INTO ai_semantic_documents (id, test_script_id, semantic_document, generated_by)
                        VALUES (CAST(:id AS UUID), CAST(:script_id AS UUID), :document, :generated_by)
                    """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "script_id": str(script_id),
                        "document": document,
                        "generated_by": generated_by,
                    },
                )
                conn.commit()
        except Exception as exc:
            logger.warning(
                "Failed to record semantic document in ai_semantic_documents: %s", exc
            )

    def get_semantic_document(self, script_id: str) -> Optional[dict]:
        self._ensure_ai_tables()
        try:
            with engine.connect() as conn:
                res = conn.execute(
                    text(
                        "SELECT semantic_document, generated_by FROM ai_semantic_documents WHERE test_script_id = CAST(:script_id AS UUID) ORDER BY created_at DESC LIMIT 1"
                    ),
                    {"script_id": str(script_id)},
                )
                row = res.first()
                if row:
                    return {
                        "semantic_document": row[0],
                        "generated_by": row[1],
                    }
                return None
        except Exception as exc:
            logger.warning("Failed to retrieve semantic document: %s", exc)
            return None

    def record_index_status(self, script_id: str, model_name: str, dimension: int):
        self._ensure_ai_tables()
        try:
            with engine.connect() as conn:
                conn.execute(
                    text(
                        """
                        INSERT INTO ai_vector_index_status (id, test_script_id, embedding_model, dimension)
                        VALUES (CAST(:id AS UUID), CAST(:script_id AS UUID), :model_name, :dimension)
                    """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "script_id": str(script_id),
                        "model_name": model_name,
                        "dimension": dimension,
                    },
                )
                conn.commit()
        except Exception as exc:
            logger.warning(
                "Failed to record index status in ai_vector_index_status: %s", exc
            )

    def list_all_script_ids(self) -> List[str]:
        try:
            with engine.connect() as conn:
                res = conn.execute(text("SELECT test_script_id FROM test_scripts"))
                return [str(row[0]) for row in res.all()]
        except Exception as exc:
            logger.error("Failed to list script ids: %s", exc)
            return []

    def list_stale_script_ids(self) -> List[str]:
        return self.list_all_script_ids()


index_repository = IndexRepository()
