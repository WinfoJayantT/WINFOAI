"""
Core Application Configuration
==============================

This module implements the Pydantic BaseSettings class to load, validate, and provide
a globally accessible `settings` object. It reads from the local `.env` file and gracefully 
falls back to sane defaults for local development.

Key Responsibilities:
  1. Environment Management: Differentiates between 'local' and 'production' profiles.
  2. Database Connection Sizing: Sets PostgreSQL connection pool constraints (Pool Size: 10).
  3. AI Model Routing: Manages API keys and Base URLs to support routing between OpenAI Cloud 
     and local Ollama inference containers.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


# ── class definition ──────────────────────────────────────────────────
class Settings(BaseSettings):
    """
    Centralized configuration registry.
    Values are automatically populated from OS environment variables or the `.env` file.
    """
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── environment ──
    ENV: str = "local"
    LOG_LEVEL: str = "INFO"

    # ── postgresql connection ──
    DATABASE_URL: str = (
        "postgresql+psycopg2://winfotest:winfotest@localhost:5432/winfotest"
    )
    DATABASE_SCHEMA: str = "public"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: float = 30.0
    DB_POOL_RECYCLE: int = 1800

    # ── qdrant vector database ──
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "winfotest_semantic_scripts"

    # ── sentence-transformer embeddings ──
    EMBEDDING_MODEL_NAME: str = "all-mpnet-base-v2"
    EMBEDDING_DIMENSION: int = 768

    # ── large language models ──
    OPENAI_API_KEY: str = ""
    LLM_API_KEY: str = "mock-ollama-key"
    LLM_MODEL: str = "qwen2.5-coder:7b"
    FAST_LLM_MODEL: str = "qwen2.5-coder:1.5b"
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    LLM_TIMEOUT_SECONDS: float = 240.0

    @property
    def is_llm_configured(self) -> bool:
        """
        Determines if the LLM inference engine is active.
        If `LLM_API_KEY` is explicitly cleared (e.g. during test suites), this acts
        as a kill-switch to enforce deterministic fallback logic.
        """
        if not self.LLM_API_KEY:
            return False
        return bool(self.OPENAI_API_KEY or self.OLLAMA_BASE_URL)


# ── singleton instantiator ────────────────────────────────────────────
@lru_cache
def get_settings() -> Settings:
    """
    Caches the settings object so `.env` parsing only happens once during startup.
    """
    return Settings()


# Global export
settings = get_settings()
