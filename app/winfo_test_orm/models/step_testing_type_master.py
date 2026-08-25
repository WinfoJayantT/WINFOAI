from sqlalchemy import Column, String, Text

from .base import Base


class StepTestingTypeMaster(Base):
    __tablename__ = "step_testing_type_master"
    testing_type_code = Column(String(50),  primary_key=True)
    testing_type_name = Column(String(255), nullable=False)
    description       = Column(Text,        nullable=True)
