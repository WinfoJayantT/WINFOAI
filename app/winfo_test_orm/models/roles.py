import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import Base


class Roles(Base):
    __tablename__ = "roles"
    
    role_id = Column(PGUUID(as_uuid=False), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    role_code = Column(String)
    role_name = Column(String, unique=True, index=True)
    role_description = Column(String)
    status_code = Column(String, ForeignKey("status_master.status_code"))
    version_no = Column(Integer)
    is_deleted = Column(Boolean, default=False)
    deleted_date = Column(DateTime)
    deleted_by = Column(PGUUID(as_uuid=False))
    creation_date = Column(DateTime)
    created_by = Column(PGUUID(as_uuid=False))
    last_update_date = Column(DateTime)
    last_updated_by = Column(PGUUID(as_uuid=False))

    status = relationship("StatusMaster", back_populates="roles")
    test_script_roles = relationship("TestScriptRoles", back_populates="role")
