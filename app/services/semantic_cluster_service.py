"""
Semantic Clustering Service
===========================

This module provides the capability to group raw database test scripts into human-readable 
categories (clusters) based on a semantic concept (e.g., "Invoice processing flows").

Key Responsibilities:
  1. Hybrid Retrieval: Uses both exact Token Matching (grouping_repository) and 
     Dense Vector Search (Qdrant) to pull all scripts related to the user's concept.
  2. Dynamic LLM Categorization: Prompts the LLM to analyze the metadata of the retrieved
     scripts and group them into logical folders/categories.
  3. Session State Hydration: Automatically registers the resulting script IDs into the 
     Conversation State so the user can seamlessly say "execute those".
"""

import logging
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from app.clients.llm_client import llm_client
from app.repositories.grouping_repository import grouping_repository
from app.schemas.cluster import ClusterRequest
from app.services.conversation_state_service import conversation_state_service
from app.services.embedding_service import embedding_service
from app.services.vector_store_service import vector_store_service
from app.core.config import settings

# ── logger initialization ───────────────────────────────────────────────
logger = logging.getLogger(__name__)


# ── structured LLM response models ────────────────────────────────────
class LLMClusterMapping(BaseModel):
    """
    Pydantic schema enforcing the exact structure we expect from the LLM when clustering.
    """
    clusters: Dict[str, List[str]] = Field(
        ..., description="Map of dynamic cluster names to arrays of test_script_number"
    )
    reasoning: str = Field(..., description="Explanation of why these clusters were chosen")


# ── prompt engineering ──────────────────────────────────────────────────
CLUSTER_SYSTEM_PROMPT = """
You are an enterprise test script categorization engine.
Given a list of test scripts, cluster them into meaningful categories based on the concept: "{concept}".
Return a JSON object with this EXACT structure:
{
  "clusters": {
    "Category Name 1": ["TEST_SCRIPT_NUMBER_A", "TEST_SCRIPT_NUMBER_B"],
    "Category Name 2": ["TEST_SCRIPT_NUMBER_C"]
  },
  "reasoning": "Brief explanation of grouping rationale"
}
Return ONLY valid JSON.
"""


# ── class definition ──────────────────────────────────────────────────
class SemanticClusterService:
    """
    Orchestrates the retrieval and semantic grouping of test scripts.
    """

    # ── primary clustering implementation ───────────────────────────────
    def cluster(
        self, request: ClusterRequest, session_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Executes the hybrid search and clustering pipeline for a given concept.
        
        Args:
            request (ClusterRequest): The schema containing the user's grouping concept.
            session_id (str): The active chat session ID to save state into.
            
        Returns:
            Dict: A structured payload mapping cluster names to Lists of database records.
        """
        logger.info(
            f"Executing high-precision hybrid clustering for concept: '{request.concept}'"
        )

        all_matched_records = []
        reasoning = ""
        
        # 1. High-Precision Database Token Matching
        precision_records = grouping_repository.search_by_tokens(request.concept)
        if precision_records:
            all_matched_records = precision_records
            reasoning = f"Retrieved via PostgreSQL database token matching for '{request.concept}'."
        else:
            # 2. Semantic Vector Fallback
            try:
                query_vector = embedding_service.embed_text(request.concept)
                hits = vector_store_service.search_similar(
                    vector=query_vector, limit=15
                )
                hit_ids = {
                    h.get("payload", {}).get("script_id") or h.get("id") for h in hits
                }
                all_recs = grouping_repository.get_dynamic_related_records()
                all_matched_records = [r for r in all_recs if str(r.get("id")) in hit_ids]
                if all_matched_records:
                    reasoning = f"Retrieved via Qdrant semantic vector similarity search for '{request.concept}'."
            except Exception as vec_exc:
                logger.warning(f"Vector search fallback failed: {vec_exc}")
                return {
                    "status": "internal_error",
                    "message": "Vector search failed.",
                    "reasoning": str(vec_exc)
                }

        if not all_matched_records:
            return {
                "status": "not_found",
                "message": f"No scripts matched the concept '{request.concept}'.",
                "reasoning": "Both exact token search and semantic search returned 0 results."
            }

        # 3. Dynamic LLM Mapping
        final_clusters: Dict[str, List[Dict[str, Any]]] = {}
        all_matched_ids: List[str] = [str(r.get("id", "")) for r in all_matched_records]
        
        if settings.is_llm_configured:
            # Prepare minimal metadata for the LLM to cluster without token exhaustion
            script_summaries = [
                {
                    "test_script_number": r.get("test_script_number"),
                    "script_name": r.get("script_name"),
                    "description": r.get("description"),
                    "module": r.get("module"),
                    "process": r.get("process")
                }
                for r in all_matched_records
            ]
            
            try:
                model_to_use = getattr(settings, "FAST_LLM_MODEL", None) or settings.LLM_MODEL
                raw_json = llm_client.generate_completion(
                    system_prompt=CLUSTER_SYSTEM_PROMPT.replace("{concept}", request.concept),
                    user_prompt=str(script_summaries),
                    temperature=0.0,
                    max_tokens=400,
                    model=model_to_use,
                    trace_id="cluster_mapping"
                )
                
                import json, re
                clean = raw_json.strip()
                if "```" in clean:
                    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean, re.DOTALL)
                    clean = m.group(1) if m else re.sub(r"```[a-z]*", "", clean).strip()

                parsed = json.loads(clean)
                
                # Normalize if top-level dictionary was directly clusters
                cluster_map = parsed.get("clusters") if isinstance(parsed.get("clusters"), dict) else parsed
                llm_reasoning = parsed.get("reasoning", f"Grouped by {request.concept}")

                # Reconstruct live database objects from the LLM's generated strings
                for cluster_name, script_nums in cluster_map.items():
                    if cluster_name == "reasoning":
                        continue
                    if not isinstance(script_nums, list):
                        continue
                    final_clusters[cluster_name] = []
                    for num in script_nums:
                        rec = next((r for r in all_matched_records if r.get("test_script_number") == num), None)
                        if rec:
                            final_clusters[cluster_name].append(rec)
                
                # Handle any unmatched scripts the LLM forgot to include
                matched_in_clusters = {s.get("id") for group in final_clusters.values() for s in group}
                unmatched = [r for r in all_matched_records if r.get("id") not in matched_in_clusters]
                if unmatched:
                    final_clusters.setdefault("Other Matched Scripts", []).extend(unmatched)

                reasoning = f"{reasoning} Clustered by AI: {llm_reasoning}"
                
            except Exception as e:
                logger.warning("LLM cluster mapping fallback to flat list: %s", e)
                final_clusters["All Matched Scripts"] = all_matched_records
                reasoning = f"{reasoning} LLM unavailable, showing flat list."
        else:
            final_clusters["All Matched Scripts"] = all_matched_records
            reasoning = f"{reasoning} LLM unconfigured, showing flat list."

        # 4. Save conversation state for follow-up execution prompts
        state = conversation_state_service.get(session_id)
        state.last_result_label = f"Clustered by '{request.concept}'"
        state.last_result_script_ids = all_matched_ids
        state.can_execute_previous_result = len(all_matched_ids) > 0
        conversation_state_service.save(state)

        return {
            "status": "success",
            "concept": request.concept,
            "clusters": final_clusters,
            "reasoning": reasoning,
            "total_scripts_matched": len(all_matched_ids),
            "tool": "semantic_cluster_scripts",
        }


# ── singleton export ──────────────────────────────────────────────────
semantic_cluster_service = SemanticClusterService()
