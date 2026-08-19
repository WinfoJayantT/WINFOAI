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
from typing import Any, Dict, List

from app.repositories.index_repository import index_repository
from app.repositories.step_repository import step_repository
from app.repositories.test_script_repository import test_script_repository
from app.services.embedding_service import embedding_service
from app.services.semantic_document_service import semantic_document_service
from app.services.vector_store_service import vector_store_service
from app.services.process_mapping_service import process_mapping_service
from app.core.config import settings

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
    def index_all(self, fast_mode: bool = True) -> Dict[str, Any]:
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

    def index_stale(self) -> Dict[str, Any]:
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
    def trigger_asynchronous_index(self, fast_mode: bool = True) -> Dict[str, Any]:
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

    def get_status(self) -> Dict[str, Any]:
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
    def _index_ids(self, script_ids: List[str], fast_mode: bool = True) -> Dict[str, Any]:
        """
        The core pipeline loop that pulls, documents, embeds, and pushes scripts to Qdrant.
        """
        indexed: List[str] = []
        failed: List[str] = []

        with self._lock:
            self.total_scripts = len(script_ids)
            self.processed_scripts = 0

        for script_id in script_ids:
            try:
                # 1. Pull raw script and ordered steps
                script = test_script_repository.get_by_id(script_id)
                if script is None:
                    failed.append(script_id)
                    with self._lock:
                        self.processed_scripts += 1
                    continue

                steps = step_repository.get_ordered_steps(script_id)

                # 2. Generate Semantic Document
                if settings.is_llm_configured and not fast_mode:
                    doc = semantic_document_service.generate_semantic_document(
                        script, steps
                    )
                    generated_by = "llm"
                else:
                    doc = semantic_document_service.generate_local_semantic_document(
                        script, steps
                    )
                    generated_by = "deterministic_fallback"

                # 3. Generate Dense Embedding Vector
                vector = embedding_service.embed_text(doc)

                # 4. Resolve Oracle Modern Best Practice (MBP) mappings
                mapping = process_mapping_service.get_mapping_for_script(script)
                mbp_metadata = {}
                if mapping:
                    mbp_metadata = {
                        "l1_process": mapping["l1_process"],
                        "l2_process": mapping["l2_process"],
                        "product_mix": mapping["product_mix"],
                        "is_covered": mapping["is_covered"]
                    }

                # 5. Push payload to Qdrant
                vector_store_service.upsert_script(
                    script_id=script_id,
                    test_script_number=script.get("test_script_number") or "N/A",
                    script_name=script.get("script_name") or script.get("name") or "N/A",
                    semantic_document=doc,
                    vector=vector,
                    metadata={
                        "module": script.get("module"),
                        "process": script.get("process"),
                        **mbp_metadata
                    },
                )
                
                # 6. Update PostgreSQL sync records
                index_repository.record_semantic_document(script_id, doc, generated_by)
                index_repository.record_index_status(
                    script_id, settings.EMBEDDING_MODEL_NAME, len(vector)
                )
                
                indexed.append(script_id)
                with self._lock:
                    self.processed_scripts += 1
                    
            except Exception as exc:
                logger.exception("Indexing failed for script_id=%s", script_id)
                failed.append(script_id)
                with self._lock:
                    self.processed_scripts += 1

        return {"indexed_script_ids": indexed, "failed_script_ids": failed}


# ── singleton export ──────────────────────────────────────────────────
indexing_service = IndexingService()
