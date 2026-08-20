from .base import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
import uuid

class TestScriptDependencies(Base):
    __tablename__ = "test_script_dependencies"
    
    test_script_dependency_id = Column(PGUUID(as_uuid=False), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    test_script_id = Column(PGUUID(as_uuid=False), ForeignKey("test_scripts.test_script_id"))
    depends_on_test_script_id = Column(PGUUID(as_uuid=False), ForeignKey("test_scripts.test_script_id"))
    creation_date = Column(DateTime)
    created_by = Column(PGUUID(as_uuid=False))

    test_script = relationship("TestScripts", foreign_keys=[test_script_id], back_populates="dependencies")
    depends_on_test_script = relationship("TestScripts", foreign_keys=[depends_on_test_script_id], back_populates="dependent_test_scripts")