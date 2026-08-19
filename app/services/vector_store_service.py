"""
Vector Store Service (Qdrant Interface)
=======================================

This module encapsulates all interactions with the Qdrant Vector Database.
It handles connection resiliency, schema provisioning, vector indexing, 
and dense similarity search operations.

Key Responsibilities:
  1. Connection Management: Maintains a persistent connection to the Qdrant instance
     defined in settings, with automatic failover to local embedded storage if remote fails.
  2. Schema Provisioning: Ensures the required `test_scripts` collection exists with
     the correct Cosine Distance and Dimensionality metrics.
  3. Payload Indexing: Upserts semantic documents alongside their 768-d neural embeddings.
  4. Search Execution: Runs dense vector queries with optional payload filters.
"""

import logging
from typing import Any, Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.config import settings

# ── logger initialization ───────────────────────────────────────────────
logger = logging.getLogger(__name__)


# ── class definition ──────────────────────────────────────────────────
class VectorStoreService:
    """
    Manages vector indexing and retrieval operations against the Qdrant vector database.
    """

    def __init__(self):
        self._client: Optional[QdrantClient] = None

    # ── connection lifecycle ────────────────────────────────────────────
    @property
    def client(self) -> QdrantClient:
        """
        Lazily initializes and returns the QdrantClient.
        Implements a robust fallback mechanism from remote to local disk storage.
        
        Returns:
            QdrantClient: The active Qdrant client instance.
            
        Raises:
            RuntimeError: If connection fails in a strict 'production' environment.
        """
        if not self._client:
            try:
                self._client = QdrantClient(url=settings.QDRANT_URL, timeout=5.0)
                # Test the connection immediately
                self._client.get_collections()
                logger.info(f"Connected to Qdrant server at {settings.QDRANT_URL}")
            except Exception as e:
                # In production, we fail fast. In dev/local, we fall back to embedded.
                if settings.ENV == "production":
                    logger.error(f"Failed to connect to Qdrant server in production: {e}")
                    raise RuntimeError(f"Qdrant connection failed in production: {e}")
                logger.warning(
                    f"Could not connect to Qdrant server ({e}). Falling back to local embedded storage ('./qdrant_local_db')."
                )
                self._client = QdrantClient(path="./qdrant_local_db")
        return self._client

    # ── schema provisioning ─────────────────────────────────────────────
    def ensure_collection(self):
        """
        Idempotently creates the target vector collection if it does not already exist.
        Ensures the collection is configured for the correct embedding dimensions and Cosine similarity.
        """
        try:
            collections = [c.name for c in self.client.get_collections().collections]
            if settings.QDRANT_COLLECTION not in collections:
                self.client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION,
                    vectors_config=models.VectorParams(
                        size=settings.EMBEDDING_DIMENSION,
                        distance=models.Distance.COSINE,
                    ),
                )
                logger.info(f"Created Qdrant collection: {settings.QDRANT_COLLECTION}")
        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection exists: {e}")

    # ── indexing operations ─────────────────────────────────────────────
    def upsert_script(
        self,
        script_id: str,
        test_script_number: str,
        script_name: str,
        semantic_document: str,
        vector: List[float],
        metadata: Dict[str, Any],
    ):
        """
        Upserts a highly-dimensional vector and its associated textual payload into the index.
        
        Args:
            script_id (str): The primary key from PostgreSQL.
            test_script_number (str): The business ID (e.g. WT-001).
            script_name (str): The human-readable title.
            semantic_document (str): The raw generated semantic markdown.
            vector (List[float]): The 768-d unit-normalized neural embedding.
            metadata (Dict): Any additional filtering attributes (e.g. module, process).
            
        Raises:
            RuntimeError: If upsert fails in a production environment.
        """
        try:
            self.ensure_collection()
            self.client.upsert(
                collection_name=settings.QDRANT_COLLECTION,
                points=[
                    models.PointStruct(
                        id=str(script_id),
                        vector=vector,
                        payload={
                            "script_id": script_id,
                            "test_script_number": test_script_number,
                            "script_name": script_name,
                            "semantic_document": semantic_document,
                            **metadata,
                        },
                    )
                ],
            )
        except Exception as exc:
            if settings.ENV == "production":
                logger.error(f"Upsert failed on remote Qdrant in production: {exc}")
                raise RuntimeError(f"Qdrant upsert failed in production: {exc}")
            
            logger.warning(f"Upsert failed on remote Qdrant: {exc}. Retrying with local fallback...")
            try:
                # Emergency fallback to local embedded database
                self._client = QdrantClient(path="./qdrant_local_db")
                self.ensure_collection()
                self._client.upsert(
                    collection_name=settings.QDRANT_COLLECTION,
                    points=[
                        models.PointStruct(
                            id=str(script_id),
                            vector=vector,
                            payload={
                                "script_id": script_id,
                                "test_script_number": test_script_number,
                                "script_name": script_name,
                                "semantic_document": semantic_document,
                                **metadata,
                            },
                        )
                    ],
                )
                logger.info(f"Successfully upserted script {test_script_number} using local fallback.")
            except Exception as local_exc:
                logger.error(f"Local Qdrant upsert failed: {local_exc}")

    # ── retrieval operations ────────────────────────────────────────────
    def search_similar(
        self,
        query_vector: Optional[List[float]] = None,
        vector: Optional[List[float]] = None,
        limit: int = 5,
        query_filter: Optional[Any] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Executes a K-Nearest Neighbors (KNN) search to find the most semantically similar points.
        
        Args:
            query_vector (List[float]): The vectorized user search query.
            vector (List[float]): Alias for query_vector (backwards compatibility).
            limit (int): Max number of hits to return.
            query_filter (Any): Optional Qdrant pre-filter object (e.g. for hard module filtering).
            
        Returns:
            List[Dict]: An array of hit dictionaries containing ID, score, and payload.
        """
        self.ensure_collection()
        vec = query_vector if query_vector is not None else vector
        if vec is None:
            return []

        results = []
        try:
            # Handle API shifts in different QdrantClient versions dynamically
            if hasattr(self.client, "search"):
                results = self.client.search(
                    collection_name=settings.QDRANT_COLLECTION,
                    query_vector=vec,
                    limit=limit,
                    query_filter=query_filter,
                )
            elif hasattr(self.client, "query_points"):
                res = self.client.query_points(
                    collection_name=settings.QDRANT_COLLECTION,
                    query=vec,
                    limit=limit,
                    query_filter=query_filter,
                )
                results = res.points
        except Exception as exc:
            if settings.ENV == "production":
                logger.error(f"Remote Qdrant search failed in production: {exc}")
                raise RuntimeError(f"Qdrant search failed in production: {exc}")
            
            logger.warning(f"Remote Qdrant search failed: {exc}. Retrying with local fallback...")
            try:
                self._client = QdrantClient(path="./qdrant_local_db")
                self.ensure_collection()
                if hasattr(self.client, "search"):
                    results = self.client.search(
                        collection_name=settings.QDRANT_COLLECTION,
                        query_vector=vec,
                        limit=limit,
                        query_filter=query_filter,
                    )
                elif hasattr(self.client, "query_points"):
                    res = self.client.query_points(
                        collection_name=settings.QDRANT_COLLECTION,
                        query=vec,
                        limit=limit,
                        query_filter=query_filter,
                    )
                    results = res.points
            except Exception as local_exc:
                logger.error(f"Local Qdrant search failed: {local_exc}")

        return [
            {"id": str(hit.id), "score": hit.score, "payload": hit.payload}
            for hit in results
        ]


# ── singleton export ──────────────────────────────────────────────────
vector_store_service = VectorStoreService()
