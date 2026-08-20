from .base import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
import uuid

class ApplicationReleases(Base):
    __tablename__ = "application_releases"
    
    application_release_id = Column(PGUUID(as_uuid=False), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(PGUUID(as_uuid=False), ForeignKey("applications.application_id"))
    release_code = Column(String)
    release_name = Column(String)
    release_start_date = Column(DateTime)
    release_end_date = Column(DateTime)
    release_notes = Column(Text)
    status_code = Column(String, ForeignKey("status_master.status_code"))
    version_no = Column(Integer)
    is_deleted = Column(Boolean, default=False)
    deleted_date = Column(DateTime)
    deleted_by = Column(PGUUID(as_uuid=False))
    creation_date = Column(DateTime)
    created_by = Column(PGUUID(as_uuid=False))
    last_update_date = Column(DateTime)
    last_updated_by = Column(PGUUID(as_uuid=False))

    application = relationship("Applications", back_populates="releases")
    status = relationship("StatusMaster", back_populates="application_releases")
    test_script_releases = relationship("TestScriptReleases", back_populates="application_release")
