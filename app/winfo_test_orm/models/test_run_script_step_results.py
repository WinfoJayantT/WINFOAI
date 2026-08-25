import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class TestRunScriptStepResults(Base):
    __tablename__ = "test_run_script_step_results"

    test_run_script_step_result_id = Column(UUID(as_uuid=False), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))

    test_run_script_step_id = Column(UUID(as_uuid=False), ForeignKey("test_run_script_steps.test_run_script_step_id"), nullable=False)
    test_run_script_id = Column(UUID(as_uuid=False), ForeignKey("test_run_scripts.test_run_script_id"), nullable=False)
    attempt_no = Column(Integer, default=1)

    step_no = Column(Integer, nullable=False)
    step_description = Column(String)
    action = Column(String)
    input_parameter = Column(String)
    input_value = Column(Text)

    execution_status_code = Column(String, ForeignKey("execution_status_master.execution_status_code"), default="PENDING")

    # Fix: `timestamp with time zone` in the live DB — see the matching fix
    # on TestRunScripts.actual_start_time/actual_end_time for why declaring
    # these as naive was actively harmful.
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    duration_ms = Column(Integer)
    retry_count = Column(Integer, default=0)

    screenshot_b64 = Column(Text)
    file_path = Column(Text)
    screenshot_upload_status = Column(Text)
    # Only ever set for execution_status_code == "FAILED" — a genuine
    # failure diagnostic. A SKIPPED step's reason belongs in skip_reason
    # below, never here (see Issue 5: skipped steps used to show error
    # messages because both shared this one column).
    error_message = Column(Text)
    # Only ever set for execution_status_code == "SKIPPED" — e.g. "skipped:
    # prior step failed". Deliberately separate from error_message so a
    # skipped step never looks like a failure diagnostic.
    skip_reason = Column(Text)
    executed_locator = Column(Text)

    creation_date = Column(DateTime(timezone=True))
    created_by = Column(UUID(as_uuid=False), nullable=False)

    test_run_script_step = relationship("TestRunScriptSteps")
    test_run_script = relationship("TestRunScripts")
    execution_status = relationship("ExecutionStatusMaster")
