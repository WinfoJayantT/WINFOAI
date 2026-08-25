import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class TestRunScripts(Base):
    __tablename__ = "test_run_scripts"

    test_run_script_id = Column(UUID(as_uuid=False), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))

    test_run_id = Column(UUID(as_uuid=False), ForeignKey("test_runs.test_run_id"), nullable=False)

    source_test_script_id = Column(UUID(as_uuid=False), ForeignKey("test_scripts.test_script_id"), nullable=False)
    source_version_no = Column(Integer, nullable=False)

    instance_no = Column(Integer, default=1)
    execution_instance_name = Column(String)

    test_script_code = Column(String, nullable=False)
    fully_qualified_name = Column(String, nullable=False)
    test_script_name = Column(String, nullable=False)
    test_script_description = Column(Text)
    test_objective = Column(Text)

    execution_order = Column(Integer, nullable=False)

    # Oracle user this specific script executes as (e.g. "FIN_IMPL"). Optional —
    # when unset, execution falls back to the test run's shared configuration_id
    # credentials. Password is never stored; it is resolved from OCI Vault at
    # run time via app/utils/keyvault.py in recording-service.
    oracle_username = Column(String(100), nullable=True)

    validation_status_code = Column(String, ForeignKey("validation_status_master.validation_status_code"), default="NOT_VALIDATED")
    execution_status_code = Column(String, ForeignKey("execution_status_master.execution_status_code"), default="PENDING")
    dependency_status_code = Column(String, default="NOT_EVALUATED")

    # Fix: these are `timestamp with time zone` in the live DB (confirmed via
    # information_schema) — declaring them as naive DateTime here caused every
    # write site to strip tzinfo before writing (see test_run_runner.py's old
    # _naive_utc_now()), which the DB session then silently reinterpreted
    # through its own timezone (Asia/Calcutta), corrupting the stored value
    # by that offset. Declaring them aware here matches the real schema and
    # lets every call site just use datetime.now(timezone.utc) directly, the
    # same way TestRuns.actual_start_time/actual_end_time already do.
    actual_start_time = Column(DateTime(timezone=True))
    actual_end_time = Column(DateTime(timezone=True))
    error_message = Column(Text)

    # Durable bounded-retry counter for scripts that fail to START (Key
    # Vault error, browser-launch crash — see ExecutionEvent.startup_failure)
    # before a single step ran. 1 = first (normal) dispatch; incremented on
    # each automatic retry. Never incremented for a script that started and
    # then genuinely failed mid-execution. See settings.MAX_SCRIPT_DISPATCH_ATTEMPTS.
    dispatch_attempts = Column(Integer, default=1)

    version_no = Column(Integer)
    is_deleted = Column(Boolean, default=False)
    deleted_date = Column(DateTime(timezone=True))
    deleted_by = Column(UUID(as_uuid=False))

    creation_date = Column(DateTime(timezone=True))
    created_by = Column(UUID(as_uuid=False), nullable=False)

    test_run = relationship("TestRuns", back_populates="test_run_scripts")
    validation_status = relationship("ValidationStatusMaster")
    execution_status = relationship("ExecutionStatusMaster")
    dependencies = relationship(
        "TestRunScriptDependencies",
        foreign_keys="TestRunScriptDependencies.test_run_script_id",
        back_populates="test_run_script",
    )
    dependent_test_run_scripts = relationship(
        "TestRunScriptDependencies",
        foreign_keys="TestRunScriptDependencies.depends_on_test_run_script_id",
        back_populates="depends_on_test_run_script",
    )
