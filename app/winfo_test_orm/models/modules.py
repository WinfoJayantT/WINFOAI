import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import Base


class Modules(Base):
    __tablename__ = "modules"
    
    module_id = Column(PGUUID(as_uuid=False), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    process_area_id = Column(PGUUID(as_uuid=False), ForeignKey("process_areas.process_area_id"))
    module_code = Column(String)
    module_name = Column(String)
    module_description = Column(String)
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

    status = relationship("StatusMaster", back_populates="modules")
    process_area = relationship("ProcessAreas", back_populates="modules")
    test_scripts = relationship("TestScripts", back_populates="module")
