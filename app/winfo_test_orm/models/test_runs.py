import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class TestRuns(Base):
    __tablename__ = "test_runs"

    test_run_id = Column(UUID(as_uuid=False), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))

    workspace_id = Column(UUID(as_uuid=False), ForeignKey("workspace.workspace_id"), nullable=False)
    configuration_id = Column(UUID(as_uuid=False), ForeignKey("workspace_configurations.workspace_configurations_id"), nullable=False)

    run_type = Column(String, default="RUN")
    template_name = Column(String)
    template_description = Column(Text)

    run_name = Column(String)
    run_description = Column(Text)

    run_status_code = Column(String, ForeignKey("run_status_master.run_status_code"), default="DRAFT")

    scheduled_start_time = Column(DateTime(timezone=True))
    actual_start_time = Column(DateTime(timezone=True))
    actual_end_time = Column(DateTime(timezone=True))
    timezone = Column(String, default="UTC")
    scheduled_time_utc = Column(DateTime(timezone=True))

    parallel_workers = Column(Integer, default=1)
    screenshot_mode = Column(String, default="all")
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=30)

    created_by = Column(UUID(as_uuid=False), nullable=False)
    executed_by = Column(UUID(as_uuid=False))

    version_no = Column(Integer)
    is_deleted = Column(Boolean, default=False)
    deleted_date = Column(DateTime(timezone=True))
    deleted_by = Column(UUID(as_uuid=False))

    creation_date = Column(DateTime(timezone=True))

    run_status = relationship("RunStatusMaster")
    test_run_scripts = relationship("TestRunScripts", back_populates="test_run")
