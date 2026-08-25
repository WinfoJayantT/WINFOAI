import uuid

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import Base


class TestScriptRoles(Base):
    __tablename__ = "test_script_roles"
    
    test_script_role_id = Column(PGUUID(as_uuid=False), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    test_script_id = Column(PGUUID(as_uuid=False), ForeignKey("test_scripts.test_script_id"))
    role_id = Column(PGUUID(as_uuid=False), ForeignKey("roles.role_id"))
    creation_date = Column(DateTime)
    created_by = Column(PGUUID(as_uuid=False))

    test_script = relationship("TestScripts", back_populates="roles")
    role = relationship("Roles", back_populates="test_script_roles")