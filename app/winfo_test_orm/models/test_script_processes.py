from .base import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
import uuid


class TestScriptProcesses(Base):
    __tablename__ = "test_script_processes"
    
    test_script_process_id = Column(PGUUID(as_uuid=False), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    test_script_id = Column(PGUUID(as_uuid=False), ForeignKey("test_scripts.test_script_id"))
    process_id = Column(PGUUID(as_uuid=False), ForeignKey("processes.process_id"))
    creation_date = Column(DateTime)
    created_by = Column(PGUUID(as_uuid=False))

    test_script = relationship("TestScripts", back_populates="processes")
    process = relationship("Processes", back_populates="test_script_processes")