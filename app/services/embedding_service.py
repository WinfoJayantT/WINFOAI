"""
WinfoTest Dense Vector Embedding Service
========================================

This module is the High-Precision Neural Vectorization Engine for the AI.

Transforms natural language text into normalized, high-dimensional dense neural vector embeddings.
Now completely offloads to Ollama API for lightning-fast GPU-accelerated inference, eliminating
blocking PyTorch CPU loads.
"""

import logging

import numpy as np

from app.clients.llm_client import LLMClient
from app.core.config import settings

# ── logger initialization ───────────────────────────────────────────────
logger = logging.getLogger(__name__)


# ── class definition ──────────────────────────────────────────────────
class EmbeddingService:
    """
    Generates high-dimensional dense neural vector embeddings for Semantic Documents
    and queries using Ollama's local API (via the OpenAI SDK wrapper).
    """

    def __init__(self, model_name: str | None = None, dimension: int | None = None):
        # We default to the settings, but this will now look for Ollama models (e.g. nomic-embed-text)
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self.llm = LLMClient()

    # ── encoding operations ─────────────────────────────────────────────
    def embed_text(self, text: str) -> list[float]:
        """
        Generates a dense vector for a single input text string using Ollama/OpenAI API.
        
        Args:
            text (str): The natural language string to vectorize.
            
        Returns:
            List[float]: A unit-normalized array of floats representing the text's semantic meaning.
            
        Raises:
            RuntimeError: If the API fails or embedding generation mathematically fails.
        """
        if not text or not text.strip():
            return [0.0] * self.dimension

        try:
            logger.debug(f"Generating embedding for text via API (model={self.model_name})")
            response = self.llm.client.embeddings.create(
                model=self.model_name,
                input=text
            )
            vector = response.data[0].embedding
            
            # Mathematical L2 Normalization
            # (Ensures Cosine Similarity == Dot Product perfectly)
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = (np.array(vector) / norm).tolist()
                
            return vector
        except Exception as e:
            error_msg = f"Embedding generation failed for text via API: {e}. Check if model '{self.model_name}' is installed (e.g. 'ollama pull {self.model_name}')."
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Efficiently generates dense vectors for a large batch of texts over the API.
        
        Args:
            texts (List[str]): Array of strings to vectorize.
            
        Returns:
            List[List[float]]: A matrix of float arrays.
        """
        if not texts:
            return []

        clean_texts = [t if (t and t.strip()) else " " for t in texts]
        
        try:
            logger.debug(f"Generating batch embeddings for {len(texts)} chunks via API (model={self.model_name})")
            response = self.llm.client.embeddings.create(
                model=self.model_name,
                input=clean_texts
            )
            
            vectors = []
            for data in response.data:
                vector = data.embedding
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = (np.array(vector) / norm).tolist()
                vectors.append(vector)
                
            return vectors
        except Exception as e:
            error_msg = f"Batch embedding generation failed: {e}. Check if model '{self.model_name}' is installed."
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e


# ── singleton export ──────────────────────────────────────────────────
embedding_service = EmbeddingService()
