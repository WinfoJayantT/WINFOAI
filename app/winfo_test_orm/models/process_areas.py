from .base import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
import uuid


class ProcessAreas(Base):
    __tablename__ = "process_areas"
    
    process_area_id = Column(PGUUID(as_uuid=False), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    stream_id = Column(PGUUID(as_uuid=False), ForeignKey("streams.stream_id"))
    process_area_code = Column(String)
    process_area_name = Column(String)
    process_area_description = Column(String)
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

    status = relationship("StatusMaster", back_populates="process_areas")
    stream = relationship("Streams", back_populates="process_areas")
    modules = relationship("Modules", back_populates="process_area")
