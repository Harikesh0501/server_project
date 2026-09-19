from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin

class Organization(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(63), unique=True, index=True, nullable=False)
    
    # Commercial Tier & Quotas
    tier: Mapped[str] = mapped_column(String(30), default="free", nullable=False) # 'free', 'pro', 'enterprise'
    max_projects: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    max_memory_mb: Mapped[int] = mapped_column(Integer, default=4096, nullable=False)

    # Active License ID (for on-premise air-gapped license validation)
    license_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

class OrganizationMember(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "organization_members"

    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), default="developer", nullable=False) # 'owner', 'admin', 'developer', 'viewer'

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_member"),
    )
