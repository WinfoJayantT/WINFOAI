from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from .base import Base


class ScriptTypeMaster(Base):
    __tablename__ = "script_type_master"

    script_type_code = Column(String, primary_key=True)
    script_type_name = Column(String)

    test_scripts = relationship("TestScripts", back_populates="script_type")
