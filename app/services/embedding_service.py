"""
================================================================================
WINFOTEST SEMANTIC DISCOVERY — DENSE VECTOR EMBEDDING SERVICE
================================================================================
Module: app.services.embedding_service
Layer: High-Precision Neural Vectorization Engine

WHAT IT DOES:
Transforms natural language text (Semantic Documents, query strings, and functional chunks)
into normalized, high-dimensional dense neural vector embeddings (768 dimensions using all-mpnet-base-v2).

HOW IT DOES IT:
1. High-Resolution Vectorization: Loads HuggingFace SentenceTransformer (all-mpnet-base-v2)
   to produce dense semantic embeddings with strict L2 unit-length normalization.
2. Strict Production Integrity: Fails fast if the neural transformer model cannot be loaded,
   preventing corrupted or uncalibrated vectors in the production vector index.
3. Dynamic Dimensionality: Automatically aligns vector dimensions with the loaded model architecture.

WHY IT WAS DESIGNED THIS WAY:
- Accuracy & Depth: all-mpnet-base-v2 provides superior semantic sentence embeddings across
  complex enterprise ERP terminology, workflow structures, and domain parameters.
- Mathematical Consistency: Unit-normalized vectors ensure that cosine similarity equals dot product.

RELATIONAL DATA MAPPING:
- Feeds: semantic_documents.embedding_json, test_script_chunks.embedding_json,
  and Qdrant collection point vectors.
================================================================================
"""

import logging
from typing import List, Optional
import numpy as np
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Generates high-dimensional, unit-normalized dense neural vector embeddings for Semantic Documents
    and queries using SentenceTransformer (all-mpnet-base-v2).
    """

    def __init__(self, model_name: Optional[str] = None, dimension: Optional[int] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self._model = None

    def _get_model(self):
        """
        Lazily loads the SentenceTransformer model on first invocation.
        """
        if self._model is not None:
            return self._model

        try:
            import os
            from sentence_transformers import SentenceTransformer
            # Force offline mode: model is already cached locally from first index run.
            # This eliminates all HuggingFace HEAD requests on every cold start.
            os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
            os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
            logger.info(f"Loading SentenceTransformer neural model: {self.model_name} (local cache only)...")
            model = SentenceTransformer(self.model_name, local_files_only=True)
            if hasattr(model, "get_embedding_dimension"):
                detected_dim = int(model.get_embedding_dimension())
                if detected_dim > 0:
                    self.dimension = detected_dim
            elif hasattr(model, "get_sentence_embedding_dimension"):
                detected_dim = int(model.get_sentence_embedding_dimension())
                if detected_dim > 0:
                    self.dimension = detected_dim
            self._model = model
            logger.info(f"SentenceTransformer model '{self.model_name}' loaded successfully (dimension={self.dimension}).")
            return self._model
        except Exception as e:
            error_msg = (
                f"CRITICAL: Failed to load SentenceTransformer neural model '{self.model_name}': {e}. "
                "Production semantic retrieval requires sentence-transformers and PyTorch."
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def embed_text(self, text: str) -> List[float]:
        """
        Generates a normalized dense vector (length = dimension) for the input text.
        Fails fast if the neural model cannot be loaded.
        """
        if not text or not text.strip():
            return [0.0] * self.dimension

        model = self._get_model()
        try:
            vector = model.encode(text, normalize_embeddings=True, show_progress_bar=False)
            if isinstance(vector, np.ndarray):
                return vector.tolist()
            return list(vector)
        except Exception as e:
            logger.error(f"SentenceTransformer encoding failed for text: {e}")
            raise RuntimeError(f"Embedding generation failed: {e}") from e

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Efficiently generates normalized dense vectors for a batch of texts.
        """
        if not texts:
            return []

        model = self._get_model()
        clean_texts = [t if (t and t.strip()) else " " for t in texts]
        vectors = model.encode(clean_texts, normalize_embeddings=True, show_progress_bar=False)
        return [v.tolist() if isinstance(v, np.ndarray) else list(v) for v in vectors]


# Module singleton instance (guaranteed non-None, models loaded on-demand)
embedding_service = EmbeddingService()
