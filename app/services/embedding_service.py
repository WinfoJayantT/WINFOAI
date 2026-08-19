"""
WinfoTest Dense Vector Embedding Service
========================================

This module is the High-Precision Neural Vectorization Engine for the AI.

Transforms natural language text (Semantic Documents, query strings, and functional chunks)
into normalized, high-dimensional dense neural vector embeddings (768 dimensions using `all-mpnet-base-v2`).

Features:
  1. High-Resolution Vectorization: Uses HuggingFace SentenceTransformer for strict L2 unit-length normalization.
  2. Strict Production Integrity: Fails fast if the neural transformer model cannot be loaded.
  3. Dynamic Dimensionality: Automatically aligns vector dimensions with the loaded model architecture.
  4. Local Caching: Forces `TRANSFORMERS_OFFLINE` to eliminate HuggingFace HTTP HEAD requests during cold starts.
"""

import logging
from typing import List, Optional
import numpy as np
from app.core.config import settings

# ── logger initialization ───────────────────────────────────────────────
logger = logging.getLogger(__name__)


# ── class definition ──────────────────────────────────────────────────
class EmbeddingService:
    """
    Generates high-dimensional, unit-normalized dense neural vector embeddings for Semantic Documents
    and queries using SentenceTransformer (all-mpnet-base-v2).
    """

    def __init__(self, model_name: Optional[str] = None, dimension: Optional[int] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self._model = None

    # ── model loading ───────────────────────────────────────────────────
    def _get_model(self):
        """
        Lazily loads the SentenceTransformer model on first invocation.
        
        Returns:
            SentenceTransformer: The loaded neural model ready for encoding.
            
        Raises:
            RuntimeError: If the model cannot be found in the local cache or loaded.
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
            
            # Dynamically infer dimensionality to prevent mismatch errors
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

    # ── encoding operations ─────────────────────────────────────────────
    def embed_text(self, text: str) -> List[float]:
        """
        Generates a normalized dense vector (length = dimension) for a single input text string.
        
        Args:
            text (str): The natural language string to vectorize.
            
        Returns:
            List[float]: A unit-normalized array of 768 floats representing the text's semantic meaning.
            
        Raises:
            RuntimeError: If the embedding generation mathematically fails.
        """
        if not text or not text.strip():
            return [0.0] * self.dimension

        model = self._get_model()
        try:
            # Generate mathematically consistent vectors where Cosine Similarity == Dot Product
            vector = model.encode(text, normalize_embeddings=True, show_progress_bar=False)
            if isinstance(vector, np.ndarray):
                return vector.tolist()
            return list(vector)
        except Exception as e:
            logger.error(f"SentenceTransformer encoding failed for text: {e}")
            raise RuntimeError(f"Embedding generation failed: {e}") from e

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Efficiently generates normalized dense vectors for a large batch of texts in parallel.
        
        Args:
            texts (List[str]): Array of strings to vectorize.
            
        Returns:
            List[List[float]]: A matrix of float arrays.
        """
        if not texts:
            return []

        model = self._get_model()
        clean_texts = [t if (t and t.strip()) else " " for t in texts]
        
        vectors = model.encode(clean_texts, normalize_embeddings=True, show_progress_bar=False)
        return [v.tolist() if isinstance(v, np.ndarray) else list(v) for v in vectors]


# ── singleton export ──────────────────────────────────────────────────
embedding_service = EmbeddingService()
