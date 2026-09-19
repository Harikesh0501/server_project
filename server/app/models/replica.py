from sqlalchemy import String, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin

class ContainerReplica(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "container_replicas"

    deployment_id: Mapped[str] = mapped_column(String(36), ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False, index=True)
    container_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    container_name: Mapped[str] = mapped_column(String(100), nullable=False)
    replica_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    private_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    port: Mapped[int] = mapped_column(Integer, default=3000, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="STARTING", nullable=False, index=True) # STARTING, HEALTHY, UNHEALTHY, TERMINATED
    health_check_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    deployment = relationship("Deployment", back_populates="replicas")

    __table_args__ = (
        Index("ix_replicas_deployment_status", "deployment_id", "status"),
    )
