import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class ScriptOutputParameter(Base):
    """
    Formally declares that a test run script step produces a named runtime value.
    At execution time the step's CaptureValue action stores this in the shared
    var_store under `parameter_name`, making it available as ${parameter_name}
    in downstream steps.
    """
    __tablename__ = "script_output_parameters"

    output_parameter_id = Column(
        UUID(as_uuid=False), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    test_run_script_id = Column(
        UUID(as_uuid=False),
        ForeignKey("test_run_scripts.test_run_script_id"),
        nullable=False,
        index=True,
    )
    # The specific step that captures this value (NULL = any step with this var name)
    source_step_id = Column(
        UUID(as_uuid=False),
        ForeignKey("test_run_script_steps.test_run_script_step_id"),
        nullable=True,
    )
    parameter_name = Column(String(255), nullable=False)
    capture_method = Column(String(50), default="TEXT_CONTENT")  # TEXT_CONTENT | FIELD_VALUE | URL_REGEX
    capture_pattern = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)

    is_deleted = Column(Boolean, default=False)
    # Fix: timestamp with time zone in the live DB — see TestRunScripts for
    # why these were declared naive incorrectly.
    creation_date = Column(DateTime(timezone=True))
    created_by = Column(UUID(as_uuid=False))

    test_run_script = relationship("TestRunScripts")
    input_dependencies = relationship(
        "StepInputDependency",
        back_populates="output_parameter",
        cascade="all, delete-orphan",
    )
