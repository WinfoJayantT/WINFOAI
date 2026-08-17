from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENV: str = "local"
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = (
        "postgresql+psycopg2://winfotest:winfotest@localhost:5432/winfotest"
    )
    DATABASE_SCHEMA: str = "public"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: float = 30.0
    DB_POOL_RECYCLE: int = 1800

    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "winfotest_semantic_scripts"

    EMBEDDING_MODEL_NAME: str = "all-mpnet-base-v2"
    EMBEDDING_DIMENSION: int = 768

    OPENAI_API_KEY: str = ""
    LLM_API_KEY: str = "mock-ollama-key"
    LLM_MODEL: str = "qwen2.5-coder:7b"
    FAST_LLM_MODEL: str = "qwen2.5-coder:1.5b"
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    LLM_TIMEOUT_SECONDS: float = 240.0

    @property
    def is_llm_configured(self) -> bool:
        # If LLM_API_KEY is empty (e.g. cleared in tests), treat LLM as unconfigured
        if not self.LLM_API_KEY:
            return False
        return bool(self.OPENAI_API_KEY or self.OLLAMA_BASE_URL)



@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
