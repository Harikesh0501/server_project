from sqlalchemy import String, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin

class DeploymentLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "deployment_logs"

    deployment_id: Mapped[str] = mapped_column(String(36), ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False, index=True)
    stream: Mapped[str] = mapped_column(String(10), default="stdout", nullable=False) # 'stdout', 'stderr', 'system'
    message: Mapped[str] = mapped_column(Text, nullable=False)

    deployment = relationship("Deployment", back_populates="logs")

    __table_args__ = (
        Index("ix_logs_deployment_created", "deployment_id", "created_at"),
    )
