from typing import Any

from app.repositories.step_repository import step_repository
from app.repositories.test_script_repository import test_script_repository
from app.services.embedding_service import embedding_service
from app.services.semantic_document_service import semantic_document_service
from app.services.vector_store_service import vector_store_service


class SimilarityService:
    """Section 12.3: compares semantic workflow meaning, not script numbers."""

    def find_similar(self, identifier: str, limit: int = 5) -> dict[str, Any]:
        script = test_script_repository.get_script_by_identifier(identifier)
        if script is None:
            return {"status": "not_found", "matches": []}

        steps = step_repository.get_ordered_steps(script["id"])
        doc = semantic_document_service.enrich_semantic_document_if_needed(None, script, steps)
        vector = embedding_service.embed_text(doc)

        matches = vector_store_service.search_similar(
            vector=vector, limit=limit, exclude_id=script["id"]
        )
        return {"status": "success", "matches": matches}


similarity_service = SimilarityService()
