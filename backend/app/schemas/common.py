"""
Common schemas used across the application.
"""
from datetime import datetime
from typing import Generic, TypeVar, List, Optional, Any
from pydantic import BaseModel, Field


T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    items: List[T]
    total: int
    page: int
    pages: int
    per_page: int


class ErrorDetail(BaseModel):
    """Error detail."""
    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    request_id: Optional[str] = None


class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = True
    message: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime


class RateLimitInfo(BaseModel):
    """Rate limit information in response headers."""
    limit: int
    remaining: int
    reset: int


class SystemHealthResponse(BaseModel):
    """System health response for admin."""
    status: str
    version: str
    build_time: str
    uptime_seconds: float
    services: dict
    system: dict


class ServerInfoResponse(BaseModel):
    """Server info response for admin."""
    version: str
    environment: str
    python_version: str
    dependencies: dict
    config: dict
    stats: dict


class RequestLogResponse(BaseModel):
    """Request log entry."""
    id: str
    user_id: Optional[str] = None
    method: str
    path: str
    status_code: int
    response_time_ms: int
    ip_address: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class RequestLogListResponse(BaseModel):
    """Paginated request logs."""
    logs: List[RequestLogResponse]
    total: int
    page: int
    pages: int


class UsageStatsResponse(BaseModel):
    """Usage statistics response."""
    tokens_used: int
    requests_count: int
    period_start: datetime
    period_end: datetime
    app_id: Optional[str] = None
    app_name: Optional[str] = None


class UsageSummaryResponse(BaseModel):
    """Usage summary for user dashboard."""
    total_tokens: int
    total_requests: int
    by_app: List[UsageStatsResponse]
    period_start: datetime
    period_end: datetime
