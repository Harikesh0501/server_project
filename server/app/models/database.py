from sqlalchemy import String, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin

class ManagedDatabase(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "managed_databases"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    engine: Mapped[str] = mapped_column(String(30), nullable=False) # 'postgres', 'redis'
    version: Mapped[str] = mapped_column(String(20), default="16", nullable=False)
    container_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    database_name: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PROVISIONING", nullable=False) # 'PROVISIONING', 'RUNNING', 'STOPPED', 'FAILED'
    connection_url_secret_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    project = relationship("Project", back_populates="databases")

    __table_args__ = (
        Index("ix_managed_databases_project_engine", "project_id", "engine"),
    )
