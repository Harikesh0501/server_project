from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin

class Secret(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "secrets"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # AES-256-GCM Encrypted Ciphertext and Initialization Vector
    encrypted_value: Mapped[str] = mapped_column(Text, nullable=False)
    nonce: Mapped[str] = mapped_column(String(64), nullable=False)

    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False) # e.g. auto-injected DATABASE_URL

    # Relationship
    project = relationship("Project", back_populates="secrets")

    __table_args__ = (
        UniqueConstraint("project_id", "key", name="uq_project_secret_key"),
    )
