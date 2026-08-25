"""
Semantic Grouping Repository
============================

This module provides the first-pass token filtering engine used by the SemanticClusterService.
Before spending expensive LLM tokens or running slow Qdrant vector searches, this DAO attempts 
to find deterministic exact matches (e.g. ERP codes like 'P2P' or 'O2C') directly from PostgreSQL.

Key Responsibilities:
  1. Token Matching: Strips conversational stop words from the user's intent and checks
     for substring matches within core script metadata (Name, Number, Description).
  2. Fallback Bridging: Acts as a bridge between the test_script_repository and the higher-level
     clustering logic to maintain single-responsibility principles.
"""

import logging
from typing import Any

# ── logger initialization ───────────────────────────────────────────────
logger = logging.getLogger(__name__)


# ── class definition ──────────────────────────────────────────────────
class GroupingRepository:
    """
    Data Access Object (DAO) for rapid, deterministic text-based script retrieval.
    """

    def get_dynamic_related_records(self) -> list[dict[str, Any]]:
        """
        Retrieves all test scripts from PostgreSQL source of truth.
        (Delegates to test_script_repository to avoid duplicated joins).
        """
        try:
            from app.repositories.test_script_repository import test_script_repository
            return test_script_repository.list_all()
        except Exception as exc:
            logger.error("Failed to query test_scripts: %s", exc)
            return []

    def search_by_tokens(self, concept: str) -> list[dict[str, Any]]:
        """
        Performs high-precision database filtering for concept keywords across script 
        identifiers and names.
        
        Args:
            concept (str): The raw user search intent (e.g. "show me all P2P scripts").
            
        Returns:
            List[Dict]: The subset of test scripts that matched the exact tokens.
        """
        records = self.get_dynamic_related_records()
        
        # 1. Strip conversational filler words to isolate the core business concepts
        STOP_WORDS = {
            "TEST", "TESTS", "SCRIPT", "SCRIPTS", "SHOW", "GIVE", "ME", 
            "STEPS", "STEP", "OF", "A", "AN", "THE", "FROM", "FOR", 
            "PERTAINING", "TO", "WITH", "ANY", "THIS", "THAT", "AND", "OR", "IN", "ON"
        }
        
        # 2. Tokenize and normalize the user input
        tokens = [t.strip().upper() for t in concept.split() if len(t.strip()) >= 2 and t.strip().upper() not in STOP_WORDS]
        if not tokens:
            return []

        precision_matches = []
        
        # 3. Scan the concatenated metadata blob of every script
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


# ── singleton export ──────────────────────────────────────────────────
grouping_repository = GroupingRepository()
