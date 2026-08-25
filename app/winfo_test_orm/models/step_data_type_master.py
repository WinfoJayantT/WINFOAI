from sqlalchemy import Column, String, Text

from .base import Base


class StepDataTypeMaster(Base):
    __tablename__ = "step_data_type_master"
    data_type_code = Column(String(50),  primary_key=True)
    data_type_name = Column(String(255), nullable=False)
    description    = Column(Text,        nullable=True)
