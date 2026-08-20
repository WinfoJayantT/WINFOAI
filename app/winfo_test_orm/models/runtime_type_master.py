from .base import Base
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship


class RuntimeTypeMaster(Base):
    __tablename__ = "runtime_type_master"

    runtime_type_code = Column(String, primary_key=True)
    runtime_type_name = Column(String)

    test_scripts = relationship("TestScripts", back_populates="runtime_type")
