import uuid
from sqlalchemy import (
    Column, String, Text, Integer, ForeignKey, TIMESTAMP, JSON, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

from app.core.config import settings

Base = declarative_base()
SCHEMA = settings.DATABASE_SCHEMA if settings.DATABASE_SCHEMA != "public" else None

class ProcessArea(Base):
    __tablename__ = "process_areas"
    __table_args__ = {"schema": SCHEMA} if SCHEMA else {}
    id = Column('process_area_id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column('process_area_name', String, unique=True, nullable=False)


class Process(Base):
    __tablename__ = "processes"
    __table_args__ = {"schema": SCHEMA} if SCHEMA else {}
    id = Column('process_id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column('process_name', String, unique=True, nullable=False)
    # Note: no process_area_id in DEV processes table directly? Wait, DEV processes DOES have it? 
    # Let's check analyze output: processes DOES NOT have process_area_id! Wait, the output for processes:
    # process_id, process_code, process_name, process_description, ...
    # So process_area_id is missing! I'll comment it out to be safe.
    # process_area_id = Column(UUID(as_uuid=True))


class Module(Base):
    __tablename__ = "modules"
    __table_args__ = {"schema": SCHEMA} if SCHEMA else {}
    id = Column('module_id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column('module_name', String, unique=True, nullable=False)


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": SCHEMA} if SCHEMA else {}
    id = Column('role_id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column('role_name', String, unique=True, nullable=False)


class Label(Base):
    __tablename__ = "labels"
    __table_args__ = {"schema": SCHEMA} if SCHEMA else {}
    id = Column('label_id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column('label_name', String, unique=True, nullable=False)


class TestScript(Base):
    __tablename__ = "test_scripts"
    __table_args__ = {"schema": SCHEMA} if SCHEMA else {}
    id = Column('test_script_id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_script_number = Column(String, unique=True, nullable=False)
    qualified_name = Column(String)
    script_name = Column(String, nullable=False)
    description = Column('script_description', Text)
    objective = Column(Text)
    module_id = Column('module_id', UUID(as_uuid=True), ForeignKey(f"{SCHEMA + '.' if SCHEMA else ''}modules.module_id"))
    created_at = Column('creation_date', TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column('last_update_date', TIMESTAMP(timezone=True), server_default=func.now())

    module = relationship("Module")


class TestRun(Base):
    __tablename__ = "test_runs"
    __table_args__ = {"schema": SCHEMA} if SCHEMA else {}
    id = Column('test_run_id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    started_at = Column('actual_start_time', TIMESTAMP(timezone=True), server_default=func.now())
    finished_at = Column('actual_end_time', TIMESTAMP(timezone=True))
    status = Column('run_status_code', String)


class TestRunScript(Base):
    __tablename__ = "test_run_scripts"
    __table_args__ = {"schema": SCHEMA} if SCHEMA else {}
    id = Column('test_run_script_id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_run_id = Column('test_run_id', UUID(as_uuid=True), ForeignKey(f"{SCHEMA + '.' if SCHEMA else ''}test_runs.test_run_id"))
    test_script_id = Column('source_test_script_id', UUID(as_uuid=True), ForeignKey(f"{SCHEMA + '.' if SCHEMA else ''}test_scripts.test_script_id"))
    status = Column('execution_status_code', String)
    started_at = Column('actual_start_time', TIMESTAMP(timezone=True))
    finished_at = Column('actual_end_time', TIMESTAMP(timezone=True))


class TestRunScriptStep(Base):
    __tablename__ = "test_run_script_steps"
    __table_args__ = {"schema": SCHEMA} if SCHEMA else {}
    id = Column('test_run_script_step_id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_run_script_id = Column('test_run_script_id', UUID(as_uuid=True), ForeignKey(f"{SCHEMA + '.' if SCHEMA else ''}test_run_scripts.test_run_script_id"))
    step_no = Column(Integer, nullable=False)
    step_action = Column('action', String)
    step_description = Column(Text)
    input_parameter = Column(String)
    default_value = Column(String)
    locator_code = Column(Text)
    fallback_locator_code = Column('locator_fallbacks', Text)


class TestRunScriptStepResult(Base):
    __tablename__ = "test_run_script_step_results"
    __table_args__ = {"schema": SCHEMA} if SCHEMA else {}
    id = Column('test_run_script_step_result_id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_run_script_step_id = Column('test_run_script_step_id', UUID(as_uuid=True), ForeignKey(f"{SCHEMA + '.' if SCHEMA else ''}test_run_script_steps.test_run_script_step_id"))
    status = Column('execution_status_code', String, nullable=False)
    error_message = Column(Text)
    dom_snapshot = Column('screenshot_b64', Text)
    executed_at = Column('ended_at', TIMESTAMP(timezone=True), server_default=func.now())


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
