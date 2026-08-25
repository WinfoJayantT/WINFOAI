import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class MasterStep(Base):
    __tablename__ = "master_steps"

    id                  = Column(UUID(as_uuid=True),  primary_key=True, default=uuid.uuid4)
    script_id           = Column(UUID(as_uuid=False), nullable=False)
    step_no             = Column(Integer,      nullable=False, default=0)
    step_description    = Column(Text,         nullable=False, default="")
    action              = Column(String(100),  nullable=False, default="Action")
    input_parameter     = Column(String(500),  nullable=True)
    input_type          = Column(String(50),   nullable=True)
    locator_code        = Column(Text,         nullable=True)
    locator_fallbacks   = Column(Text,         nullable=True)
    # Which shape locator_code/locator_fallbacks are in, since a step with
    # no verified locator legitimately has both columns null (Login/Open
    # Task/Navigation, or failed verification). 'action_json' — the normal
    # action-dispatch locator dictionary (XPath string or JSON get_by_*
    # chain); 'legacy_capture' — CaptureValue's own dedicated raw-selector
    # format, not a get_by_* chain. See CHANGELOG.md.
    locator_format       = Column(String(30),   nullable=True)
    default_value       = Column(Text,         nullable=True)
    wait_ms             = Column(Integer,      nullable=False, default=0)
    is_dropdown_open    = Column(Boolean,      nullable=False, default=False)
    is_option_selection = Column(Boolean,      nullable=False, default=False)
    take_screenshot     = Column(Boolean,      nullable=False, default=True)
    is_active           = Column(Boolean,      nullable=False, default=True)
    is_manual           = Column(Boolean,      nullable=False, default=False)
    is_mandatory        = Column(Boolean,      nullable=False, default=False)
    is_unique           = Column(Boolean,      nullable=False, default=False)
    validation_type     = Column(String(50),   nullable=False, default="NOT_APPLICABLE")
    validation_name     = Column(String(255),  nullable=True)
    data_type           = Column(String(50),   nullable=True)
    testing_type        = Column(String(50),   nullable=False, default="NOT_APPLICABLE")
    created_at          = Column(DateTime(timezone=True), server_default=func.now())
    updated_at          = Column(DateTime(timezone=True), server_default=func.now())
