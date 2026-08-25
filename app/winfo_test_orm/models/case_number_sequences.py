import uuid

from sqlalchemy import Column, Integer
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class CaseNumberSequence(Base):
    __tablename__ = "case_number_sequences"

    id              = Column(UUID(as_uuid=True),  primary_key=True, default=uuid.uuid4)
    process_area_id = Column(UUID(as_uuid=False), nullable=False)
    module_id       = Column(UUID(as_uuid=False), nullable=True)
    next_seq        = Column(Integer, nullable=False, default=1)
