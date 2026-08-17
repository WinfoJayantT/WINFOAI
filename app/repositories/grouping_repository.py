# STREAMING_CHUNK:Initializing grouping repository with high-precision database token matching...
import logging
from typing import Any, Dict, List
from sqlalchemy import text
from app.core.config import settings
from app.repositories.db import engine

logger = logging.getLogger(__name__)


class GroupingRepository:
    def get_dynamic_related_records(self) -> List[Dict[str, Any]]:
        """Retrieves all test scripts from PostgreSQL source of truth."""
        try:
            from app.repositories.test_script_repository import test_script_repository
            return test_script_repository.list_all()
        except Exception as exc:
            logger.error("Failed to query test_scripts: %s", exc)
            return []

    def search_by_tokens(self, concept: str) -> List[Dict[str, Any]]:
        """Performs high-precision database filtering for concept keywords across script identifiers and names."""
        records = self.get_dynamic_related_records()
        STOP_WORDS = {"TEST", "TESTS", "SCRIPT", "SCRIPTS", "SHOW", "GIVE", "ME", "STEPS", "STEP", "OF", "A", "AN", "THE", "FROM", "FOR", "PERTAINING", "TO", "WITH", "ANY", "THIS", "THAT", "AND", "OR", "IN", "ON"}
        tokens = [t.strip().upper() for t in concept.split() if len(t.strip()) >= 2 and t.strip().upper() not in STOP_WORDS]
        if not tokens:
            return []

        precision_matches = []
        for r in records:
            number = str(r.get("test_script_number") or "").upper()
            qualified = str(r.get("qualified_name") or "").upper()
            name = str(r.get("script_name") or "").upper()
            desc = str(r.get("description") or "").upper()

            blob = f"{number} {qualified} {name} {desc}"

            # Check if any token matches precisely as an ERP code or substring
            if any(token in blob for token in tokens):
                precision_matches.append(r)

        return precision_matches


grouping_repository = GroupingRepository()
