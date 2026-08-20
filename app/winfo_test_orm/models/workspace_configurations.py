import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class WorkspaceConfiguration(Base):
    __tablename__ = "workspace_configurations"

    workspace_configurations_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    configuration: Mapped[str] = mapped_column(String(150), nullable=False)
    smtp_form: Mapped[str] = mapped_column(String(150), nullable=False)
    parameters: Mapped[dict | None] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=True
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    created_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    row_version: Mapped[int] = mapped_column(
        Integer, server_default=text("1"), nullable=False
    )
