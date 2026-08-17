# STREAMING_CHUNK:Initializing vector store service with robust search compatibility...
import logging
from typing import Any, Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    def __init__(self):
        self._client: Optional[QdrantClient] = None

    @property
    def client(self) -> QdrantClient:
        if not self._client:
            try:
                self._client = QdrantClient(url=settings.QDRANT_URL, timeout=5.0)
                self._client.get_collections()
                logger.info(f"Connected to Qdrant server at {settings.QDRANT_URL}")
            except Exception as e:
                if settings.ENV == "production":
                    logger.error(f"Failed to connect to Qdrant server in production: {e}")
                    raise RuntimeError(f"Qdrant connection failed in production: {e}")
                logger.warning(
                    f"Could not connect to Qdrant server ({e}). Falling back to local embedded storage ('./qdrant_local_db')."
                )
                self._client = QdrantClient(path="./qdrant_local_db")
        return self._client

    def ensure_collection(self):
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

    def upsert_script(
        self,
        script_id: str,
        test_script_number: str,
        script_name: str,
        semantic_document: str,
        vector: List[float],
        metadata: Dict[str, Any],
    ):
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

    def search_similar(
        self,
        query_vector: Optional[List[float]] = None,
        vector: Optional[List[float]] = None,
        limit: int = 5,
        query_filter: Optional[Any] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        self.ensure_collection()
        vec = query_vector if query_vector is not None else vector
        if vec is None:
            return []

        results = []
        try:
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


vector_store_service = VectorStoreService()
