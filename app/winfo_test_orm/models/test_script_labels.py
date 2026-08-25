import uuid

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import Base


class TestScriptLabels(Base):
    __tablename__ = "test_script_labels"
    
    test_script_label_id = Column(PGUUID(as_uuid=False), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    test_script_id = Column(PGUUID(as_uuid=False), ForeignKey("test_scripts.test_script_id"))
    label_id = Column(PGUUID(as_uuid=False), ForeignKey("labels.label_id"))
    creation_date = Column(DateTime)
    created_by = Column(PGUUID(as_uuid=False))

    test_script = relationship("TestScripts", back_populates="labels")
    label = relationship("Labels", back_populates="test_script_labels")