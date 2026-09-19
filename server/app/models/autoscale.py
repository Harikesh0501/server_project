from sqlalchemy import String, Integer, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin

class AutoscaleEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "autoscale_events"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    deployment_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("deployments.id", ondelete="CASCADE"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False) # 'SCALE_UP', 'SCALE_DOWN'
    old_replicas: Mapped[int] = mapped_column(Integer, nullable=False)
    new_replicas: Mapped[int] = mapped_column(Integer, nullable=False)
    trigger_reason: Mapped[str] = mapped_column(String(255), nullable=False)
    cpu_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_percent: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (
        Index("ix_autoscale_project_created", "project_id", "created_at"),
    )
