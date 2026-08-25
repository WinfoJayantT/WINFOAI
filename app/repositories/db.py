"""
Database Session Management
===========================

The ONLY module allowed to open SQLAlchemy sessions (per PROJECT_CONTEXT_FINAL.md).
All AI domain services must go through repository layer methods to access PostgreSQL data.
Direct `db.session` usage or raw SQL execution from outside the `app/repositories/` directory
is strictly prohibited.

Key Responsibilities:
  1. Connection Pooling: Configures `SQLAlchemy` pool sizing and ping-checks to handle high 
     concurrency from the FastAPI backend.
  2. Transaction Contexts: Provides the `get_session` context manager for safe commit/rollback lifecycles.
"""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# ── engine initialization ───────────────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,  # Crucial for preventing connection drops in long-running AI tasks
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


# ── session lifecycle ───────────────────────────────────────────────────
@contextmanager
def get_session() -> Iterator[Session]:
    """
    Provides a transactional scope around a series of database operations.
    
    Yields:
        Session: An active SQLAlchemy database session.
        
    Raises:
        Exception: Re-raises any exception after safely rolling back the transaction.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
