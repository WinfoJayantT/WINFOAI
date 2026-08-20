from .base import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid


class Schedules(Base):
    __tablename__ = "schedules"

    schedule_id = Column(UUID(as_uuid=False), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))

    test_run_id = Column(UUID(as_uuid=False), ForeignKey("test_runs.test_run_id"), nullable=False)

    schedule_name = Column(String, nullable=False)
    schedule_description = Column(Text)

    cron_expression = Column(String)
    scheduled_at = Column(DateTime)
    timezone = Column(String, default="UTC")

    is_enabled = Column(Boolean, default=True)

    last_run_at = Column(DateTime)
    last_run_status_code = Column(String, ForeignKey("run_status_master.run_status_code"))
    next_run_at = Column(DateTime)
    run_count = Column(Integer, default=0)

    version_no = Column(Integer)
    is_deleted = Column(Boolean, default=False)
    deleted_date = Column(DateTime)
    deleted_by = Column(UUID(as_uuid=False))

    creation_date = Column(DateTime)
    created_by = Column(UUID(as_uuid=False), nullable=False)
    last_update_date = Column(DateTime)
    last_updated_by = Column(UUID(as_uuid=False))

    test_run = relationship("TestRuns")
    last_run_status = relationship("RunStatusMaster")
