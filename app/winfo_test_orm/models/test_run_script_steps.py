import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class TestRunScriptSteps(Base):
    __tablename__ = "test_run_script_steps"

    test_run_script_step_id = Column(UUID(as_uuid=False), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))

    test_run_script_id = Column(UUID(as_uuid=False), ForeignKey("test_run_scripts.test_run_script_id"), nullable=False)
    source_master_step_id = Column(UUID(as_uuid=False))

    step_no = Column(Integer, nullable=False)
    step_description = Column(Text, default="")
    action = Column(String, default="Action")
    input_parameter = Column(String)
    input_type = Column(String)
    locator_code = Column(Text)
    locator_fallbacks = Column(Text)
    # See MasterStep.locator_format's docstring — copied at snapshot time,
    # same as locator_code/locator_fallbacks. See CHANGELOG.md.
    locator_format = Column(String(30))
    default_value = Column(Text)
    wait_ms = Column(Integer, default=0)
    take_screenshot = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    is_manual = Column(Boolean, default=False)
    is_mandatory    = Column(Boolean,     default=False)
    is_unique       = Column(Boolean,     default=False)
    validation_type = Column(String(50),  default="NOT_APPLICABLE")
    validation_name = Column(String(255), nullable=True)
    data_type       = Column(String(50),  nullable=True)
    testing_type    = Column(String(50),  default="NOT_APPLICABLE")
    is_injected = Column(Boolean, default=False)
    is_modified = Column(Boolean, default=False)

    version_no = Column(Integer)
    is_deleted = Column(Boolean, default=False)
    # Fix: timestamp with time zone in the live DB — see the matching fix on
    # TestRunScripts for why these were declared naive incorrectly.
    deleted_date = Column(DateTime(timezone=True))
    deleted_by = Column(UUID(as_uuid=False))

    creation_date = Column(DateTime(timezone=True))
    created_by = Column(UUID(as_uuid=False), nullable=False)
    last_update_date = Column(DateTime(timezone=True))
    last_updated_by = Column(UUID(as_uuid=False))

    test_run_script = relationship("TestRunScripts")
