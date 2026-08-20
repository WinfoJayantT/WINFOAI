from sqlalchemy import Column, String, Text, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import datetime
from .base import Base


class Action(Base):
    __tablename__ = "wt_actions"

    action_id = Column(UUID(as_uuid=True), primary_key=True, default=text("gen_random_uuid()"))
    action_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    creation_date = Column(DateTime, default=datetime.datetime.utcnow)
    last_update_date = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    last_updated_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
