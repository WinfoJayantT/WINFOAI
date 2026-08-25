from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class RunStatusMaster(Base):
    __tablename__ = "run_status_master"

    run_status_code = Column(String, primary_key=True, index=True)
    run_status_name = Column(String)
    run_status_description = Column(String)
    is_terminal = Column(Boolean, default=False)
    display_order = Column(Integer)
    status_code = Column(String, ForeignKey("status_master.status_code"))
    version_no = Column(Integer)
    is_deleted = Column(Boolean, default=False)
    deleted_date = Column(DateTime)
    deleted_by = Column(UUID(as_uuid=False))
    creation_date = Column(DateTime)
    created_by = Column(UUID(as_uuid=False))
    last_update_date = Column(DateTime)
    last_updated_by = Column(UUID(as_uuid=False))
