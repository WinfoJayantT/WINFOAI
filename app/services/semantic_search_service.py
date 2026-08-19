"""
Semantic Search Service
=======================

This module implements the primary search engine for finding existing WinfoTest scripts.
It uses a highly tuned Hybrid Retrieval architecture that combines the strengths of 
both modern LLM-based vector similarity and traditional database keyword matching.

Key Responsibilities:
  1. Dense Vector Search (Qdrant): Finds scripts using semantic meaning (e.g., "Procure to Pay" matches "P2P").
  2. Keyword Matching (PostgreSQL): Identifies exact overlaps of tokenized test script names and numbers.
  3. Hybrid Scoring: Merges the scores, boosting scripts that match both semantically and literally.
  4. Entity Rehydration: Resolves final search IDs directly against the PostgreSQL source of truth
     before returning payloads to the user interface.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from qdrant_client.http import models as qdrant_models

from app.services.embedding_service import embedding_service
from app.services.vector_store_service import vector_store_service
from app.repositories.test_script_repository import test_script_repository
from app.repositories.grouping_repository import grouping_repository
from app.repositories.step_repository import step_repository
from app.services.semantic_document_service import semantic_document_service
from app.services.debug_trace_service import debug_trace_service

# ── logger initialization ───────────────────────────────────────────────
logger = logging.getLogger(__name__)


# ── class definition ──────────────────────────────────────────────────
class SemanticSearchService:
    """
    Executes hybrid (Vector + Keyword) search queries against the test script inventory.
    """

    # ── primary search implementation ───────────────────────────────────
    def search(
        self,
        query: str,
        limit: int = 5,
        include_steps: bool = False,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes a dual-pipeline semantic search.
        
        Args:
            query (str): The natural language search query.
            limit (int): The max number of top results to return.
            include_steps (bool): Whether to hydrate all steps for the top results.
            filters (Dict): Optional Qdrant `FieldCondition` filters (e.g. strict module matching).
            
        Returns:
            Dict: Result payload containing the top N matched scripts and their rehydrated database records.
        """
        logger.info(f"Performing strict semantic vector search for query: '{query}', filters: {filters}")
        
        start_time = time.perf_counter()
        trace = debug_trace_service.start_trace()
        trace.detected_intent = "semantic_search_tests"
        trace.selected_tool = "semantic_search_tests"
        trace.parsed_arguments = {
            "query": query,
            "limit": limit,
            "include_steps": include_steps,
            "filters": filters
        }
        
        results = []

        try:
            # 1. Compile Qdrant Filter conditions if filters are present
            qdrant_filter = None
            if filters:
                conditions = []
                for key, val in filters.items():
                    # Support boolean matching, string matching, or case-insensitive matching
                    if isinstance(val, bool):
                        conditions.append(
                            qdrant_models.FieldCondition(
                                key=key, match=qdrant_models.MatchValue(value=val)
                            )
                        )
                    else:
                        conditions.append(
                            qdrant_models.FieldCondition(
                                key=key, match=qdrant_models.MatchValue(value=str(val))
                            )
                        )
                if conditions:
                    qdrant_filter = qdrant_models.Filter(must=conditions)

            # 2. Dense Vector Search (from Qdrant Index)
            vector = embedding_service.embed_text(query)
            trace.vector_search_used = True
            
            # Fetch double the limit to allow re-ranking after hybrid merge
            hits = vector_store_service.search_similar(
                vector=vector, limit=limit * 2, query_filter=qdrant_filter
            )

            # 3. Database Keyword/Token Match (from PostgreSQL Source of Truth)
            db_matches = grouping_repository.search_by_tokens(query)
            debug_trace_service.attach_repository_call(
                trace, "grouping_repository.search_by_tokens", len(db_matches)
            )
            
            # Extract query tokens for keyword overlap scoring
            stop_words = {"TEST", "TESTS", "SCRIPT", "SCRIPTS", "SHOW", "FIND", "ME", "FOR", "AND", "OR", "IN", "THE", "OF", "A", "AN"}
            query_tokens = [t.strip().upper() for t in query.split() if len(t.strip()) >= 2 and t.strip().upper() not in stop_words]

            # 4. Hybrid Merging and Calibrated Scoring
            merged_results = {}
            
            # Process Dense Vector hits
            for hit in hits:
                payload = hit.get("payload", {})
                script_id = str(payload.get("script_id") or hit.get("id"))
                raw_score = float(hit.get("score") or 0.0)
                
                # Calibrate all-mpnet-base-v2 cosine score (0.40 - 0.85) to high-precision 0.70 - 0.98 scale
                calibrated_vector = min(0.96, max(0.60, 0.65 + ((raw_score - 0.35) / 0.50) * 0.30)) if raw_score > 0 else 0.0
                
                merged_results[script_id] = {
                    "id": script_id,
                    "score": calibrated_vector,
                    "vector_score": calibrated_vector,
                    "vector_match": True,
                    "db_match": False,
                    "kw_score": 0.0,
                }

            # Process Keyword matches
            for db_rec in db_matches:
                script_id = str(db_rec.get("id") or db_rec.get("test_script_id"))
                
                # Calculate keyword overlap ratio
                blob = f"{db_rec.get('test_script_number', '')} {db_rec.get('script_name', '')} {db_rec.get('module', '')} {db_rec.get('process', '')} {db_rec.get('qualified_name', '')}".upper()
                matched_count = sum(1 for tok in query_tokens if tok in blob)
                overlap_ratio = (matched_count / len(query_tokens)) if query_tokens else 0.5
                
                if overlap_ratio >= 1.0:
                    kw_score = 0.94
                elif overlap_ratio >= 0.5:
                    kw_score = 0.88
                else:
                    kw_score = 0.82

                if script_id in merged_results:
                    merged_results[script_id]["db_match"] = True
                    merged_results[script_id]["kw_score"] = kw_score
                    # Dual Agreement Boost: High vector similarity + direct keyword presence
                    merged_results[script_id]["score"] = min(0.98, max(merged_results[script_id]["vector_score"], kw_score) + 0.05)
                else:
                    merged_results[script_id] = {
                        "id": script_id,
                        "score": kw_score,
                        "vector_score": 0.0,
                        "vector_match": False,
                        "db_match": True,
                        "kw_score": kw_score,
                    }

            # 5. Sort and Limit results
            sorted_items = sorted(
                merged_results.values(), key=lambda x: x["score"], reverse=True
            )[:limit]

            # 6. Hydrate from PostgreSQL database (re-loading live entities)
            for idx, item in enumerate(sorted_items):
                script_id = item["id"]
                script_data = test_script_repository.get_by_id(script_id)
                debug_trace_service.attach_repository_call(
                    trace, "test_script_repository.get_by_id", 1 if script_data else 0
                )
                
                if not script_data:
                    continue

                steps = step_repository.get_ordered_steps(script_id)
                debug_trace_service.attach_repository_call(
                    trace, "step_repository.get_ordered_steps", len(steps)
                )

                # Dynamically retrieve or generate the semantic document from PostgreSQL/LLM
                # to satisfy "Final responses must reload entities from PostgreSQL. NEVER produce responses from vector payloads alone."
                doc = semantic_document_service.get_or_create_semantic_document(
                    script_data, steps, only_allow_cache=(idx > 0)
                )
                
                if include_steps and steps:
                    doc += "\n\n### Step Breakdown\n"
                    for i, step in enumerate(steps, start=1):
                        action = step.get('action') or step.get('step_action') or ''
                        doc += f"**Step {i}:** {action}\n"

                results.append(
                    {
                        "id": script_id,
                        "score": item["score"],
                        "test_script_number": script_data.get("test_script_number") or "N/A",
                        "script_name": script_data.get("script_name") or "Unknown",
                        "semantic_document": doc,
                        "database_record": {**script_data, "steps": steps},
                    }
                )
        except Exception as exc:
            logger.error(f"Vector search execution failed: {exc}")
            trace.errors.append(str(exc))

        debug_trace_service.finish_trace(trace, start_time)

        if not results:
            return {
                "status": "not_found",
                "query": query,
                "results": [],
                "total_results": 0,
                "reasoning": f"No semantically indexed test scripts found matching '{query}'. Please run the indexing service to populate the vector store.",
                "tool": "semantic_search_tests",
                "debug_trace": trace.to_dict(),
            }

        return {
            "status": "success",
            "query": query,
            "results": results,
            "total_results": len(results),
            "reasoning": f"Found {len(results)} semantically matched test scripts for '{query}'.",
            "tool": "semantic_search_tests",
            "debug_trace": trace.to_dict(),
        }


# ── singleton export ──────────────────────────────────────────────────
semantic_search_service = SemanticSearchService()
