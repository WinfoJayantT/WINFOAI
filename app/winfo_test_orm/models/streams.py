import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import Base


class Streams(Base):
    __tablename__ = "streams"
    
    stream_id = Column(PGUUID(as_uuid=False), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(PGUUID(as_uuid=False), ForeignKey("applications.application_id"))
    stream_name = Column(String)
    stream_description = Column(String)
    stream_code = Column(String)
    status_code = Column(String, ForeignKey("status_master.status_code"))
    display_sequence = Column(Integer)
    version_no = Column(Integer)
    is_deleted = Column(Boolean, default=False)
    deleted_date = Column(DateTime)
    deleted_by = Column(PGUUID(as_uuid=False))
    creation_date = Column(DateTime)
    created_by = Column(PGUUID(as_uuid=False))
    last_update_date = Column(DateTime)
    last_updated_by = Column(PGUUID(as_uuid=False))

    application = relationship("Applications", back_populates="streams")
    status = relationship("StatusMaster", back_populates="streams")
    process_areas = relationship("ProcessAreas", back_populates="stream")
