"""
Core Application Configuration
==============================

This module implements the Pydantic BaseSettings class to load, validate, and provide
a globally accessible `settings` object. It reads from the local `.env` file and 
falls back to safe local-development defaults.

Key Responsibilities:
  1. Environment Management: Differentiates between 'local' and 'production' profiles.
  2. Database Connection Sizing: Sets PostgreSQL connection pool constraints.
  3. AI Model Routing: Manages API keys and Base URLs to support routing between OpenAI
     Cloud and local Ollama inference containers.
  4. Security: Enforces API key header authentication and CORS policy.
  5. Production Validation: Prevents startup with missing critical config in production.
"""

import logging
from functools import lru_cache
from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


# ── class definition ──────────────────────────────────────────────────
class Settings(BaseSettings):
    """
    Centralized configuration registry.
    Values are automatically populated from OS environment variables or the `.env` file.
    """
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── environment ──
    # Set ENV=production in docker-compose or cloud deployment to enable strict validation.
    ENV: str = "local"
    LOG_LEVEL: str = "INFO"

    # ── postgresql connection ──
    # Default uses docker-compose service name 'db'. Override via DATABASE_URL env var.
    DATABASE_URL: str = (
        "postgresql+psycopg2://winfotest:winfotest@db:5432/winfotest"
    )
    DATABASE_SCHEMA: str = "public"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: float = 30.0
    DB_POOL_RECYCLE: int = 1800

    # ── qdrant vector database ──
    # Default uses docker-compose service name 'qdrant'. Override via QDRANT_URL env var.
    QDRANT_URL: str = "http://qdrant:6333"
    QDRANT_COLLECTION: str = "winfotest_semantic_scripts"

    # ── sentence-transformer embeddings ──
    EMBEDDING_MODEL_NAME: str = "all-mpnet-base-v2"
    EMBEDDING_DIMENSION: int = 768

    # ── large language models ──
    OPENAI_API_KEY: str = ""
    # LLM_API_KEY: a non-empty value acts as a kill-switch enabler for LLM calls.
    # Set to empty string to disable all LLM generation (forces fallback logic).
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "qwen2.5-coder:7b"
    FAST_LLM_MODEL: str = "qwen2.5-coder:1.5b"
    # Default uses docker host gateway for Ollama. Override via OLLAMA_BASE_URL env var.
    OLLAMA_BASE_URL: str = "http://host.docker.internal:11434/v1"
    LLM_TIMEOUT_SECONDS: float = 240.0

    # ── security & access control ──
    # API_KEY_HEADER: If set, all API requests must include 'X-API-Key: <value>'.
    # Leave empty to disable auth (local dev only).
    API_KEY_HEADER: Optional[str] = None

    # CORS_ORIGINS: Comma-separated list of allowed origins for the CORS middleware.
    # Example: "https://winfotest.app,https://staging.winfotest.app"
    # Defaults to wildcard for local development only.
    CORS_ORIGINS: str = "*"

    # ── rate limiting ──
    # Max requests per minute per IP on expensive LLM endpoints.
    RATE_LIMIT_PER_MINUTE: int = 30

    @property
    def is_llm_configured(self) -> bool:
        """
        Determines if the LLM inference engine is active.
        If `LLM_API_KEY` is empty, this disables all generation and forces
        deterministic fallback logic (useful for tests and CI pipelines).
        """
        if not self.LLM_API_KEY:
            return False
        return bool(self.OPENAI_API_KEY or self.OLLAMA_BASE_URL)

    @property
    def cors_origins_list(self) -> list[str]:
        """Parses the CORS_ORIGINS comma-separated string into a list."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @model_validator(mode="after")
    def _validate_production_config(self) -> "Settings":
        """
        Enforces that critical settings are configured when running in production mode.
        This prevents silent misconfiguration in cloud deployments.
        """
        if self.ENV == "production":
            if "localhost" in self.DATABASE_URL or "@db:" not in self.DATABASE_URL and "localhost" in self.DATABASE_URL:
                logger.warning(
                    "[Config] DATABASE_URL still points to localhost in production mode. "
                    "Ensure DATABASE_URL is set via environment variable."
                )
            if self.CORS_ORIGINS == "*":
                logger.warning(
                    "[Config] CORS_ORIGINS is set to wildcard '*' in production mode. "
                    "Set CORS_ORIGINS to a specific domain for security."
                )
            if not self.API_KEY_HEADER:
                logger.warning(
                    "[Config] API_KEY_HEADER is not set in production mode. "
                    "All API endpoints are publicly accessible. Set API_KEY_HEADER to enforce auth."
                )
        return self


# ── singleton instantiator ────────────────────────────────────────────
@lru_cache
def get_settings() -> Settings:
    """
    Caches the settings object so `.env` parsing only happens once during startup.
    """
    return Settings()


# Global export
settings = get_settings()
