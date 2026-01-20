"""
Marketplace app models.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class AppStatus(str, enum.Enum):
    """Marketplace app approval status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class AppCategory(str, enum.Enum):
    """Marketplace app categories."""
    PRODUCTIVITY = "productivity"
    DEVELOPMENT = "development"
    COMMUNICATION = "communication"
    DATA_ANALYSIS = "data_analysis"
    CONTENT = "content"
    AUTOMATION = "automation"
    INTEGRATION = "integration"
    OTHER = "other"


class MarketplaceApp(Base):
    """Marketplace AI application model."""
    
    __tablename__ = "marketplace_apps"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    short_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Developer
    developer_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # MCP Connection
    mcp_endpoint: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    mcp_api_key_encrypted: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    
    # Metadata
    icon_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    category: Mapped[AppCategory] = mapped_column(
        SQLEnum(AppCategory),
        default=AppCategory.OTHER,
        nullable=False
    )
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Status
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[AppStatus] = mapped_column(
        SQLEnum(AppStatus),
        default=AppStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Versioning
    version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    
    # Permissions & Capabilities
    permissions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    capabilities: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Documentation
    documentation_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    support_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    privacy_policy_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    # Moderation
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Stats
    install_count: Mapped[int] = mapped_column(default=0)
    
    # Relationships
    developer: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="developed_apps",
        foreign_keys=[developer_id]
    )
    versions: Mapped[List["AppVersion"]] = relationship(
        "AppVersion",
        back_populates="app",
        cascade="all, delete-orphan"
    )
    user_enablements: Mapped[List["UserEnabledApp"]] = relationship(
        "UserEnabledApp",
        back_populates="app",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<MarketplaceApp {self.slug}>"


class AppVersion(Base):
    """Version history for marketplace apps."""
    
    __tablename__ = "app_versions"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    app_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("marketplace_apps.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    mcp_endpoint: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    changelog: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    app: Mapped["MarketplaceApp"] = relationship("MarketplaceApp", back_populates="versions")
    
    def __repr__(self) -> str:
        return f"<AppVersion {self.app_id}:{self.version}>"


class UserEnabledApp(Base):
    """Tracks which apps users have enabled."""
    
    __tablename__ = "user_enabled_apps"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    app_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("marketplace_apps.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    granted_permissions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    enabled_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="enabled_apps")
    app: Mapped["MarketplaceApp"] = relationship("MarketplaceApp", back_populates="user_enablements")
    
    def __repr__(self) -> str:
        return f"<UserEnabledApp user={self.user_id[:8]} app={self.app_id[:8]}>"
