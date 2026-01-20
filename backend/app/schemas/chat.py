"""
Chat and conversation schemas.
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field

from app.models.chat import MessageRole


class MessageCreate(BaseModel):
    """Schema for creating a message."""
    content: str = Field(..., min_length=1, max_length=50000)
    
    
class MessageResponse(BaseModel):
    """Schema for message response."""
    id: str
    conversation_id: str
    role: MessageRole
    content: str
    tool_calls: Optional[List[dict]] = None
    tool_name: Optional[str] = None
    app_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    """Schema for creating a conversation."""
    title: Optional[str] = Field(None, max_length=255)


class ConversationResponse(BaseModel):
    """Schema for conversation response."""
    id: str
    title: Optional[str] = None
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    
    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    """Detailed conversation with messages."""
    messages: List[MessageResponse] = []


class ChatRequest(BaseModel):
    """Schema for chat request."""
    message: str = Field(..., min_length=1, max_length=50000)
    conversation_id: Optional[str] = None


class ToolCall(BaseModel):
    """Schema for tool call in response."""
    id: str
    name: str
    app_id: str
    app_name: str
    arguments: dict
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None


class ChatResponse(BaseModel):
    """Schema for chat response."""
    conversation_id: str
    message: MessageResponse
    tool_calls: Optional[List[dict]] = None


class ConversationListResponse(BaseModel):
    """Schema for paginated conversation list."""
    conversations: List[ConversationResponse]
    total: int
    page: int
    pages: int
