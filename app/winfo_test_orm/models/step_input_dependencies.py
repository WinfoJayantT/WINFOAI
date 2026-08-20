from .base import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid


class StepInputDependency(Base):
    """
    Formally declares that a step in one script consumes a named output
    produced by a step in another script.

    At execution time, before the consumer step runs, the runtime substitutes
    ${parameter_name} in the step's default_value / input_parameter with the
    captured value from var_store.
    """
    __tablename__ = "step_input_dependencies"

    input_dependency_id = Column(
        UUID(as_uuid=False), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    # The script + step that USES the value
    consumer_script_id = Column(
        UUID(as_uuid=False),
        ForeignKey("test_run_scripts.test_run_script_id"),
        nullable=False,
        index=True,
    )
    consumer_step_id = Column(
        UUID(as_uuid=False),
        ForeignKey("test_run_script_steps.test_run_script_step_id"),
        nullable=False,
    )
    # The declared output this dependency resolves to
    output_parameter_id = Column(
        UUID(as_uuid=False),
        ForeignKey("script_output_parameters.output_parameter_id"),
        nullable=False,
    )
    # Convenience copy — the name the step must use as ${parameter_name}
    parameter_name = Column(String(255), nullable=False)
    # Which field gets the injected value: default_value | input_parameter | locator_code
    target_field = Column(String(50), default="default_value")

    is_deleted = Column(Boolean, default=False)
    # Fix: timestamp with time zone in the live DB — see TestRunScripts for
    # why these were declared naive incorrectly.
    creation_date = Column(DateTime(timezone=True))
    created_by = Column(UUID(as_uuid=False))

    consumer_script = relationship("TestRunScripts")
    output_parameter = relationship("ScriptOutputParameter", back_populates="input_dependencies")
