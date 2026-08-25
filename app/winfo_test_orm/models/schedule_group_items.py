from datetime import datetime

from sqlalchemy import UUID, Boolean, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ScheduleGroupItem(Base):
    __tablename__ = "sch_schedule_group_items"

    schedule_group_item_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    schedule_group_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sch_schedule_groups.schedule_group_id", ondelete="CASCADE"), nullable=False)
    test_run_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    creation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
    created_by: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    last_updated_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_updated_by: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    deleted_by: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    deleted_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    item_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    execution_order: Mapped[int | None] = mapped_column(Integer, nullable=True)


    # Relationship to ScheduleGroup
    schedule_group = relationship("ScheduleGroup", back_populates="schedule_group_items")