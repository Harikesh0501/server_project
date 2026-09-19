from sqlalchemy import String, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin

class Project(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Subdomain is strictly unique across the platform (e.g., 'my-shop' -> 'my-shop.deploy.local')
    subdomain: Mapped[str] = mapped_column(String(63), unique=True, index=True, nullable=False)
    
    # Optional Custom Vanity Domain (e.g., 'deploy.mycompany.com')
    custom_domain: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)

    # Runtime & Framework Metadata
    framework: Mapped[str] = mapped_column(String(50), default="unknown", nullable=False)
    runtime_type: Mapped[str] = mapped_column(String(20), default="frontend", nullable=False) # 'frontend', 'backend', 'monorepo'

    # Git Repository Details
    git_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    git_branch: Mapped[str] = mapped_column(String(100), default="main", nullable=False)
    root_directory: Mapped[str] = mapped_column(String(255), default="./", nullable=False)

    # Commands & Ports
    install_command: Mapped[str | None] = mapped_column(String(255), nullable=True)
    build_command: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_command: Mapped[str | None] = mapped_column(String(255), nullable=True)
    port: Mapped[int] = mapped_column(Integer, default=3000, nullable=False)

    # Autoscaling Configuration
    min_replicas: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    max_replicas: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    target_cpu_percent: Mapped[int] = mapped_column(Integer, default=75, nullable=False)

    # User / Tenant Link
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    # Relationships
    deployments = relationship("Deployment", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    secrets = relationship("Secret", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    databases = relationship("ManagedDatabase", back_populates="project", cascade="all, delete-orphan", lazy="selectin")

