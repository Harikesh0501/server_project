from sqlalchemy import String, Integer, Float, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin

class Deployment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "deployments"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Git & Build Provenance
    commit_hash: Mapped[str | None] = mapped_column(String(40), nullable=True)
    commit_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    branch: Mapped[str] = mapped_column(String(100), default="main", nullable=False)

    # Status State Machine: PENDING -> BUILDING -> HEALTH_CHECKING -> ACTIVE -> SUPERSEDED / FAILED
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False, index=True)
    
    # Local Registry Image Tag
    image_tag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Active Replicas serving traffic
    active_replicas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    build_duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Diagnostics & Error Details
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    project = relationship("Project", back_populates="deployments")
    replicas = relationship("ContainerReplica", back_populates="deployment", cascade="all, delete-orphan", lazy="selectin")
    logs = relationship("DeploymentLog", back_populates="deployment", cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        Index("ix_deployments_project_status", "project_id", "status"),
    )

