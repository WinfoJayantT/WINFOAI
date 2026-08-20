from .base import Base
from sqlalchemy import Column, String, Text


class StepValidationTypeMaster(Base):
    __tablename__ = "step_validation_type_master"
    validation_type_code = Column(String(50),  primary_key=True)
    validation_type_name = Column(String(255), nullable=False)
    description          = Column(Text,        nullable=True)
