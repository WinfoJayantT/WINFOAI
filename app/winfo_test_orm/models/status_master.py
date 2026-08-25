from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from .base import Base


class StatusMaster(Base):
    __tablename__ = "status_master"
    status_code = Column(String, primary_key=True, index=True)
    status_name = Column(String)

    applications = relationship("Applications", back_populates="status")
    process_areas = relationship("ProcessAreas", back_populates="status")
    modules = relationship("Modules", back_populates="status")
    roles = relationship("Roles", back_populates="status")
    streams = relationship("Streams", back_populates="status")
    labels = relationship("Labels", back_populates="status")
    test_scripts = relationship("TestScripts", back_populates="status")
    application_releases = relationship("ApplicationReleases", back_populates="status")
