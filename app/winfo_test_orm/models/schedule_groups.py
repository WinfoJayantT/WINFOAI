from datetime import datetime

from sqlalchemy import UUID, Boolean, DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

# from uuid import UUID


class ScheduleGroup(Base):
    __tablename__ = "sch_schedule_groups"

    schedule_group_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    workspace_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    schedule_group_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    schedule_group_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    scheduled_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    schedule_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    creation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
    created_by: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    last_updated_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_updated_by: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    scheduled_time_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    schedule_group_items = relationship(
        "ScheduleGroupItem", back_populates="schedule_group", cascade="all, delete-orphan", passive_deletes=True
    )