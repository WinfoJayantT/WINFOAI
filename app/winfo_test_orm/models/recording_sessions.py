import uuid

from sqlalchemy import Column, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from .base import Base


class RecordingSession(Base):
    __tablename__ = "recording_sessions"

    id               = Column(UUID(as_uuid=True),  primary_key=True, default=uuid.uuid4)
    script_id        = Column(UUID(as_uuid=False), nullable=False)
    session_key      = Column(String(255), nullable=False, unique=True)
    status           = Column(String(50),  nullable=False, default="active")
    browser          = Column(String(50),  nullable=False, default="chromium")
    target_url       = Column(Text,        nullable=False)
    started_at       = Column(DateTime(timezone=True), server_default=func.now())
    ended_at         = Column(DateTime(timezone=True))
    session_metadata = Column("session_metadata", JSONB, nullable=True)
