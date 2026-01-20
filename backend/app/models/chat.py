"""
Chat and conversation models.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import String, DateTime, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class MessageRole(str, enum.Enum):
    """Message sender role."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Conversation(Base):
    """Chat conversation model."""
    
    __tablename__ = "conversations"
    
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
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_archived: Mapped[bool] = mapped_column(default=False)
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
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    
    @property
    def message_count(self) -> int:
        return len(self.messages)
    
    def __repr__(self) -> str:
        return f"<Conversation {self.id[:8]}...>"


class Message(Base):
    """Chat message model."""
    
    __tablename__ = "messages"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role: Mapped[MessageRole] = mapped_column(
        SQLEnum(MessageRole),
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Tool calls (for assistant messages that invoke tools)
    tool_calls: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    
    # Tool response (for tool messages)
    tool_call_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tool_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # App that provided the response (if from marketplace app)
    app_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("marketplace_apps.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Token usage
    prompt_tokens: Mapped[Optional[int]] = mapped_column(nullable=True)
    completion_tokens: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Metadata
    message_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    
    def __repr__(self) -> str:
        return f"<Message {self.role.value}:{self.id[:8]}...>"
