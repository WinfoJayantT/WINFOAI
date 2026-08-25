import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class ScheduleRuns(Base):
    __tablename__ = "schedule_runs"

    schedule_run_id = Column(UUID(as_uuid=False), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))

    schedule_id = Column(UUID(as_uuid=False), ForeignKey("schedules.schedule_id"), nullable=False)
    test_run_id = Column(UUID(as_uuid=False), ForeignKey("test_runs.test_run_id"))

    run_status_code = Column(String, ForeignKey("run_status_master.run_status_code"))

    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    error_message = Column(Text)

    creation_date = Column(DateTime)
    created_by = Column(UUID(as_uuid=False), nullable=False)

    schedule = relationship("Schedules")
    test_run = relationship("TestRuns")
    run_status = relationship("RunStatusMaster")
