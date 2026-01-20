"""
Marketplace app schemas.
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, HttpUrl, field_validator
import re

from app.models.app import AppStatus, AppCategory


class AppCreate(BaseModel):
    """Schema for creating a marketplace app."""
    name: str = Field(..., min_length=3, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    short_description: Optional[str] = Field(None, max_length=500)
    mcp_endpoint: str = Field(..., max_length=512)
    mcp_api_key: Optional[str] = Field(None, max_length=512)
    category: AppCategory = AppCategory.OTHER
    icon_url: Optional[str] = Field(None, max_length=512)
    documentation_url: Optional[str] = Field(None, max_length=512)
    support_email: Optional[str] = Field(None, max_length=255)
    privacy_policy_url: Optional[str] = Field(None, max_length=512)
    permissions: Optional[List[str]] = None
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v
    
    @field_validator('mcp_endpoint')
    @classmethod
    def validate_endpoint(cls, v: str) -> str:
        if not v.startswith(('http://', 'https://')):
            raise ValueError('MCP endpoint must be a valid HTTP(S) URL')
        return v


class AppUpdate(BaseModel):
    """Schema for updating a marketplace app."""
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    short_description: Optional[str] = Field(None, max_length=500)
    mcp_endpoint: Optional[str] = Field(None, max_length=512)
    mcp_api_key: Optional[str] = Field(None, max_length=512)
    category: Optional[AppCategory] = None
    icon_url: Optional[str] = Field(None, max_length=512)
    documentation_url: Optional[str] = Field(None, max_length=512)
    support_email: Optional[str] = Field(None, max_length=255)
    privacy_policy_url: Optional[str] = Field(None, max_length=512)
    permissions: Optional[List[str]] = None
    version: Optional[str] = Field(None, max_length=50)


class AppResponse(BaseModel):
    """Schema for app response."""
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    developer_id: Optional[str] = None
    category: AppCategory
    icon_url: Optional[str] = None
    is_public: bool
    is_builtin: bool
    status: AppStatus
    version: str
    permissions: Optional[List[str]] = None
    documentation_url: Optional[str] = None
    install_count: int
    created_at: datetime
    updated_at: datetime
    
    @field_validator('permissions', mode='before')
    @classmethod
    def extract_permissions(cls, v):
        """Extract permissions list from dict if stored as {'scopes': [...]}."""
        if v is None:
            return None
        if isinstance(v, dict):
            return v.get('scopes', [])
        if isinstance(v, list):
            return v
        return None
    
    class Config:
        from_attributes = True


class AppDetailResponse(AppResponse):
    """Detailed app response with additional fields."""
    support_email: Optional[str] = None
    privacy_policy_url: Optional[str] = None
    capabilities: Optional[dict] = None
    developer_name: Optional[str] = None


class AppListResponse(BaseModel):
    """Schema for paginated app list."""
    apps: List[AppResponse]
    total: int
    page: int
    pages: int
    per_page: int


class AppEnableRequest(BaseModel):
    """Schema for enabling an app."""
    app_id: str
    granted_permissions: Optional[List[str]] = None


class AppModerationRequest(BaseModel):
    """Schema for app moderation (approve/reject)."""
    status: AppStatus
    rejection_reason: Optional[str] = Field(None, max_length=1000)


class EnabledAppResponse(BaseModel):
    """Response for user's enabled apps."""
    id: str
    app: AppResponse
    granted_permissions: Optional[List[str]] = None
    enabled_at: datetime
    
    @field_validator('granted_permissions', mode='before')
    @classmethod
    def extract_granted_permissions(cls, v):
        """Extract permissions list from dict if stored as {'scopes': [...]}."""
        if v is None:
            return None
        if isinstance(v, dict):
            return v.get('scopes', [])
        if isinstance(v, list):
            return v
        return None
    
    class Config:
        from_attributes = True
