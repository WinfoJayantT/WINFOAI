from .base import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid


class TestRunScriptDependencies(Base):
    __tablename__ = "test_run_script_dependencies"

    test_run_script_dependency_id = Column(UUID(as_uuid=False), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))

    test_run_script_id = Column(UUID(as_uuid=False), ForeignKey("test_run_scripts.test_run_script_id"), nullable=False)
    depends_on_test_run_script_id = Column(UUID(as_uuid=False), ForeignKey("test_run_scripts.test_run_script_id"), nullable=False)

    dependency_source = Column(String, nullable=False)
    source_test_script_dependency_id = Column(UUID(as_uuid=False))

    version_no = Column(Integer)
    is_deleted = Column(Boolean, default=False)
    # Fix: timestamp with time zone in the live DB — see the matching fix on
    # TestRunScripts for why these were declared naive incorrectly.
    deleted_date = Column(DateTime(timezone=True))
    deleted_by = Column(UUID(as_uuid=False))

    creation_date = Column(DateTime(timezone=True))
    created_by = Column(UUID(as_uuid=False), nullable=False)

    test_run_script = relationship(
        "TestRunScripts", foreign_keys=[test_run_script_id], back_populates="dependencies"
    )
    depends_on_test_run_script = relationship(
        "TestRunScripts", foreign_keys=[depends_on_test_run_script_id], back_populates="dependent_test_run_scripts"
    )
