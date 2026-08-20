from .base import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, TSVECTOR
from sqlalchemy.orm import relationship
import uuid


class TestScripts(Base):
    __tablename__ = "test_scripts"
    
    test_script_id = Column(PGUUID(as_uuid=False), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    module_id = Column(PGUUID(as_uuid=False), ForeignKey("modules.module_id"))
    # Nullable: unlike TestRuns.configuration_id (NOT NULL), existing scripts
    # predate this column and have no configuration assigned yet. Absent
    # configuration_id is a legitimate state — see step_edit_manager.py's
    # Oracle URL resolution, which falls back to settings.ORACLE_ERP_URL
    # when this is null rather than treating it as an error.
    configuration_id = Column(PGUUID(as_uuid=False), ForeignKey("workspace_configurations.workspace_configurations_id"), nullable=True)
    test_script_number = Column(String)
    qualified_name = Column(String)
    script_name = Column(String)
    script_description = Column(Text)
    objective = Column(Text)
    agent_intent_name = Column(String)
    search_document = Column(Text)
    search_vector = Column(TSVECTOR)  # populated by DB trigger fn_build_test_script_search_document
    script_type_code = Column(String, ForeignKey("script_type_master.script_type_code"))
    runtime_type_code = Column(String, ForeignKey("runtime_type_master.runtime_type_code"))
    estimated_duration_seconds = Column(Integer)
    display_sequence = Column(Integer)
    status_code = Column(String, ForeignKey("status_master.status_code"))
    version_no = Column(Integer)
    is_deleted = Column(Boolean, default=False)
    deleted_date = Column(DateTime)
    deleted_by = Column(PGUUID(as_uuid=False))
    creation_date = Column(DateTime)
    created_by = Column(PGUUID(as_uuid=False))
    last_update_date = Column(DateTime)
    last_updated_by = Column(PGUUID(as_uuid=False))

    status = relationship("StatusMaster", back_populates="test_scripts")
    module = relationship("Modules", back_populates="test_scripts")
    script_type = relationship("ScriptTypeMaster", back_populates="test_scripts")
    runtime_type = relationship("RuntimeTypeMaster", back_populates="test_scripts")

    releases = relationship("TestScriptReleases", back_populates="test_script")
    roles = relationship("TestScriptRoles", back_populates="test_script")
    processes = relationship("TestScriptProcesses", back_populates="test_script")
    labels = relationship("TestScriptLabels", back_populates="test_script")
    dependencies = relationship("TestScriptDependencies", foreign_keys="TestScriptDependencies.test_script_id", back_populates="test_script")
    dependent_test_scripts = relationship("TestScriptDependencies", foreign_keys="TestScriptDependencies.depends_on_test_script_id", back_populates="depends_on_test_script")
