"""
Semantic Indexing Service
=========================

This module orchestrates the background extraction, generation, and embedding of test scripts 
from PostgreSQL into the Qdrant vector database.

Key Responsibilities:
  1. Batch Synchronization: Pulls raw scripts from PostgreSQL and passes them to the SemanticDocumentService.
  2. Asynchronous Execution: Runs massive LLM-generation and vector embedding tasks in a background
     daemon thread to prevent HTTP timeouts in the FastAPI layer.
  3. Fault Tolerance & Progress Tracking: Uses thread-safe locks to track `total_scripts` vs `processed_scripts`,
     recording failures without crashing the entire batch operation.
  4. MBP Meta-Tagging: Enriches the final Qdrant payload with Oracle Modern Best Practice metadata.
"""

import logging
import threading
from typing import Any

from app.core.config import settings
from app.repositories.index_repository import index_repository
from app.repositories.step_repository import step_repository
from app.repositories.test_script_repository import test_script_repository
from app.services.embedding_service import embedding_service
from app.services.process_mapping_service import process_mapping_service
from app.services.semantic_document_service import semantic_document_service
from app.services.vector_store_service import vector_store_service

# ── logger initialization ───────────────────────────────────────────────
logger = logging.getLogger(__name__)


# ── class definition ──────────────────────────────────────────────────
class IndexingService:
    """
    Manages background bulk indexing operations bridging PostgreSQL and Qdrant.
    """

    def __init__(self):
        self.is_indexing = False
        self.total_scripts = 0
        self.processed_scripts = 0
        self._lock = threading.Lock()

    # ── synchronous indexing entries ────────────────────────────────────
    def index_all(self, fast_mode: bool = True) -> dict[str, Any]:
        """
        Synchronously indexes all known scripts in the database.
        
        Args:
            fast_mode (bool): If True, skips LLM calls and uses ultra-fast native string formatting.
            
        Returns:
            Dict: Contains arrays of successfully indexed and failed script IDs.
        """
        with self._lock:
            if self.is_indexing:
                return {
                    "indexed_script_ids": [], 
                    "failed_script_ids": [], 
                    "status": "success", 
                    "message": "Indexing is already running in the background.", 
                    "indexing_in_progress": True
                }
            self.is_indexing = True

        try:
            result = self._index_ids(index_repository.list_all_script_ids(), fast_mode=fast_mode)
            return result
        finally:
            with self._lock:
                self.is_indexing = False

    def index_stale(self) -> dict[str, Any]:
        """
        Synchronously indexes only scripts that have not been indexed with the current model version.
        """
        with self._lock:
            if self.is_indexing:
                return {
                    "indexed_script_ids": [], 
                    "failed_script_ids": [], 
                    "status": "success", 
                    "message": "Indexing is already running in the background.", 
                    "indexing_in_progress": True
                }
            self.is_indexing = True

        try:
            result = self._index_ids(index_repository.list_stale_script_ids())
            return result
        finally:
            with self._lock:
                self.is_indexing = False

    # ── asynchronous triggering ─────────────────────────────────────────
    def trigger_asynchronous_index(self, fast_mode: bool = True) -> dict[str, Any]:
        """
        Spawns a daemon thread to execute `index_all`, allowing the HTTP request to return immediately.
        
        Args:
            fast_mode (bool): If True, bypasses LLM and uses local formatting for speed.
            
        Returns:
            Dict: Status message indicating the thread was successfully spawned.
        """
        with self._lock:
            if self.is_indexing:
                return {
                    "status": "success",
                    "message": "Semantic indexing is already running in the background.",
                    "indexing_in_progress": True
                }
        
        # Start indexing in a background thread to prevent API timeouts
        thread = threading.Thread(target=self.index_all, kwargs={"fast_mode": fast_mode})
        thread.daemon = True
        thread.start()
        
        mode_str = "Fast Mode (Local Deterministic)" if fast_mode else "Rich Mode (LLM Generation)"
        return {
            "status": "success",
            "message": f"Semantic indexing task successfully started in the background using {mode_str}.",
            "indexing_in_progress": True
        }

    def get_status(self) -> dict[str, Any]:
        """
        Returns the real-time progress of the active indexing thread.
        """
        with self._lock:
            return {
                "is_indexing": self.is_indexing,
                "processed_scripts": self.processed_scripts,
                "total_scripts": self.total_scripts
            }

    # ── core orchestration loop ─────────────────────────────────────────
    def _index_ids(self, script_ids: list[str], fast_mode: bool = True, batch_size: int = 64) -> dict[str, Any]:
        """
        High-throughput batch pipeline that pulls, documents, embeds, and pushes scripts to Qdrant
        in vectorized chunks of 64 scripts per database/embedding/upsert round-trip.
        """
        indexed: list[str] = []
        failed: list[str] = []

        with self._lock:
            self.total_scripts = len(script_ids)
            self.processed_scripts = 0

        # Process in chunks of batch_size (e.g. 64 scripts per round-trip)
        for i in range(0, len(script_ids), batch_size):
            chunk_ids = script_ids[i:i + batch_size]
            try:
                # 1. Bulk fetch scripts from PostgreSQL in 1 query
                scripts_map = test_script_repository.get_by_ids(chunk_ids)
                
                # 2. Bulk fetch ordered steps for all scripts in chunk in 1 query
                steps_map = step_repository.get_ordered_steps_for_scripts(chunk_ids)
                
                # 3. Generate Semantic Documents in memory
                docs_to_embed: list[str] = []
                valid_items: list[dict[str, Any]] = []
                
                for sid in chunk_ids:
                    script = scripts_map.get(str(sid))
                    if not script:
                        failed.append(sid)
                        continue
                    
                    steps = steps_map.get(str(sid), [])
                    
                    if settings.is_llm_configured and not fast_mode:
                        try:
                            doc = semantic_document_service.generate_semantic_document(script, steps)
                            generated_by = "llm"
                        except Exception:
                            doc = semantic_document_service.generate_local_semantic_document(script, steps)
                            generated_by = "deterministic_fallback"
                    else:
                        doc = semantic_document_service.generate_local_semantic_document(script, steps)
                        generated_by = "deterministic_fallback"
                    
                    mapping = process_mapping_service.get_mapping_for_script(script)
                    mbp_metadata = {}
                    if mapping:
                        mbp_metadata = {
                            "l1_process": mapping["l1_process"],
                            "l2_process": mapping["l2_process"],
                            "product_mix": mapping["product_mix"],
                            "is_covered": mapping["is_covered"]
                        }
                    
                    item = {
                        "script_id": sid,
                        "test_script_number": script.get("test_script_number") or "N/A",
                        "script_name": script.get("script_name") or script.get("name") or "N/A",
                        "semantic_document": doc,
                        "generated_by": generated_by,
                        "metadata": {
                            "module": script.get("module"),
                            "process": script.get("process"),
                            **mbp_metadata
                        }
                    }
                    valid_items.append(item)
                    docs_to_embed.append(doc)

                if valid_items:
                    # 4. Batch Vector Embedding via GPU/Ollama in 1 single matrix call
                    vectors = embedding_service.embed_batch(docs_to_embed)
                    
                    for idx, it in enumerate(valid_items):
                        it["vector"] = vectors[idx]

                    # 5. Bulk Upsert points into Qdrant in 1 single API call
                    vector_store_service.upsert_batch_scripts(valid_items)

                    # 6. Bulk Record sync status in PostgreSQL in 1 single transaction
                    status_records = [
                        {
                            "script_id": it["script_id"],
                            "document": it["semantic_document"],
                            "generated_by": it["generated_by"],
                            "model_name": settings.EMBEDDING_MODEL_NAME,
                            "dimension": len(it["vector"]),
                        }
                        for it in valid_items
                    ]
                    index_repository.record_batch_index_status(status_records)

                    indexed.extend([it["script_id"] for it in valid_items])

            except Exception as exc:
                logger.exception("Batch indexing failed for chunk starting at index %d: %s", i, exc)
                failed.extend(chunk_ids)
            finally:
                with self._lock:
                    self.processed_scripts += len(chunk_ids)

        return {"indexed_script_ids": indexed, "failed_script_ids": failed}


# ── singleton export ──────────────────────────────────────────────────
indexing_service = IndexingService()
