import uuid

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

from app.core.config import settings

Base = declarative_base()
SCHEMA = settings.DATABASE_SCHEMA if settings.DATABASE_SCHEMA != "public" else None

# --- WinfoTest Core tables ---

# --- AI-owned tables (section 29) ---

class AiSemanticDocument(Base):
    __tablename__ = "ai_semantic_documents"
    __table_args__ = {"schema": SCHEMA} if SCHEMA else {}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_script_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA + '.' if SCHEMA else ''}test_scripts.test_script_id"))
    semantic_document = Column(Text, nullable=False)
    generated_by = Column(String, nullable=False)  # 'llm' | 'deterministic_fallback'
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class AiVectorIndexStatus(Base):
    __tablename__ = "ai_vector_index_status"
    __table_args__ = {"schema": SCHEMA} if SCHEMA else {}
    test_script_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA + '.' if SCHEMA else ''}test_scripts.test_script_id"), primary_key=True)
    embedding_model = Column(String, nullable=False)
    embedding_dimension = Column(Integer, nullable=False)
    indexed_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    source_updated_at = Column(TIMESTAMP(timezone=True))


class AiConversationSession(Base):
    __tablename__ = "ai_conversation_sessions"
    __table_args__ = {"schema": SCHEMA} if SCHEMA else {}
    session_id = Column(String, primary_key=True)
    state_json = Column(JSON, nullable=False, default=dict)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class AiChatMessage(Base):
    __tablename__ = "ai_chat_messages"
    __table_args__ = {"schema": SCHEMA} if SCHEMA else {}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, ForeignKey(f"{SCHEMA + '.' if SCHEMA else ''}ai_conversation_sessions.session_id"), nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now())



class AiToolAuditLog(Base):
    __tablename__ = "ai_tool_audit_logs"
    __table_args__ = {"schema": SCHEMA} if SCHEMA else {}
    audit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now())
    session_id = Column(String)
    user_id = Column(String)
    intent = Column(String)
    tool_name = Column(String, nullable=False)
    arguments_json = Column(JSON)
    status = Column(String, nullable=False)
    records_returned = Column(Integer)
    duration_ms = Column(Integer)
    error_message = Column(Text)
    trace_id = Column(String)
