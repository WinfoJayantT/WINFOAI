import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import Base


class Applications(Base):
    __tablename__ = "applications"
    
    application_id = Column(PGUUID(as_uuid=False), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    application_code = Column(String, unique=True, index=True)
    application_name = Column(String)
    application_description = Column(Text)
    vendor_name = Column(String)
    status_code = Column(String, ForeignKey("status_master.status_code"))
    version_no = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_date = Column(DateTime(timezone=True))
    deleted_by = Column(PGUUID(as_uuid=False))
    creation_date = Column(DateTime(timezone=True))
    created_by = Column(PGUUID(as_uuid=False))
    last_update_date = Column(DateTime(timezone=True))
    last_updated_by = Column(PGUUID(as_uuid=False))

    status = relationship("StatusMaster", back_populates="applications")
    streams = relationship("Streams", back_populates="application")
    releases = relationship("ApplicationReleases", back_populates="application")
