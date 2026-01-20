"""
Audit, logging, and usage models.
"""
import uuid
from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.database import Base


class AuditAction(str, enum.Enum):
    """Audit log action types."""
    # Auth
    LOGIN = "login"
    LOGOUT = "logout"
    SIGNUP = "signup"
    PASSWORD_CHANGE = "password_change"
    TOKEN_REFRESH = "token_refresh"
    
    # Apps
    APP_ENABLED = "app_enabled"
    APP_DISABLED = "app_disabled"
    APP_CREATED = "app_created"
    APP_UPDATED = "app_updated"
    APP_DELETED = "app_deleted"
    APP_APPROVED = "app_approved"
    APP_REJECTED = "app_rejected"
    
    # Tool calls
    TOOL_INVOKED = "tool_invoked"
    TOOL_ERROR = "tool_error"
    
    # Admin
    USER_SUSPENDED = "user_suspended"
    USER_ACTIVATED = "user_activated"
    ROLE_CHANGED = "role_changed"
    CONFIG_CHANGED = "config_changed"


class AuditLog(Base):
    """Audit log for security and compliance."""
    
    __tablename__ = "audit_logs"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    app_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("marketplace_apps.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(AuditAction),
        nullable=False,
        index=True
    )
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog {self.action.value} at {self.created_at}>"


class UsageStats(Base):
    """Usage statistics per user per app."""
    
    __tablename__ = "usage_stats"
    
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
    app_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("marketplace_apps.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    requests_count: Mapped[int] = mapped_column(Integer, default=0)
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    def __repr__(self) -> str:
        return f"<UsageStats user={self.user_id[:8]} tokens={self.tokens_used}>"


class RequestLog(Base):
    """API request logs for admin monitoring."""
    
    __tablename__ = "request_logs"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    request_body_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    def __repr__(self) -> str:
        return f"<RequestLog {self.method} {self.path} {self.status_code}>"


class RateLimitConfig(Base):
    """Rate limit configuration (database-backed for dynamic updates)."""
    
    __tablename__ = "rate_limit_config"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    scope: Mapped[str] = mapped_column(String(50), nullable=False)  # 'ip', 'user', 'tool'
    identifier: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # specific user/tool
    requests_per_minute: Mapped[int] = mapped_column(Integer, default=60)
    requests_per_hour: Mapped[int] = mapped_column(Integer, default=1000)
    burst_size: Mapped[int] = mapped_column(Integer, default=10)
    is_active: Mapped[bool] = mapped_column(default=True)
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
    
    def __repr__(self) -> str:
        return f"<RateLimitConfig {self.scope}:{self.identifier}>"
