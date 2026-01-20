"""
Developer portal endpoints for app management.
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import re

from app.database import get_db
from app.models.user import User
from app.models.app import MarketplaceApp, AppVersion, AppStatus, AppCategory
from app.models.audit import AuditLog, AuditAction
from app.schemas.app import (
    AppCreate,
    AppUpdate,
    AppResponse,
    AppDetailResponse,
    AppListResponse,
)
from dataclasses import asdict
from app.api.deps import require_auth, require_developer, get_client_ip
from app.core.security import sanitize_input, encrypt_value
from app.mcp.client import mcp_client


router = APIRouter(prefix="/developer", tags=["Developer Portal"])


def generate_slug(name: str, suffix: str = "") -> str:
    """Generate a URL-friendly slug from name."""
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    if suffix:
        slug = f"{slug[:90]}-{suffix}"
    return slug[:100]


@router.get("/apps", response_model=AppListResponse)
async def list_my_apps(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: Optional[AppStatus] = None,
    user: User = Depends(require_developer),
    db: AsyncSession = Depends(get_db)
):
    """List apps created by the current developer."""
    query = select(MarketplaceApp).where(MarketplaceApp.developer_id == user.id)
    
    if status_filter:
        query = query.where(MarketplaceApp.status == status_filter)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Paginate
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(MarketplaceApp.created_at.desc())
    
    result = await db.execute(query)
    apps = result.scalars().all()
    
    return AppListResponse(
        apps=[AppResponse.model_validate(app) for app in apps],
        total=total,
        page=page,
        pages=(total + per_page - 1) // per_page,
        per_page=per_page
    )


@router.post("/apps", response_model=AppResponse, status_code=status.HTTP_201_CREATED)
async def create_app(
    app_data: AppCreate,
    request: Request,
    user: User = Depends(require_developer),
    db: AsyncSession = Depends(get_db)
):
    """Create a new marketplace app."""
    # Generate slug
    base_slug = app_data.slug or generate_slug(app_data.name)
    slug = base_slug
    
    # Ensure unique slug
    counter = 1
    while True:
        result = await db.execute(
            select(MarketplaceApp).where(MarketplaceApp.slug == slug)
        )
        if not result.scalar_one_or_none():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Encrypt MCP API key if provided
    encrypted_key = None
    if app_data.mcp_api_key:
        encrypted_key = encrypt_value(app_data.mcp_api_key)
    
    # Fetch capabilities from MCP endpoint
    capabilities = {}
    if app_data.mcp_endpoint:
        # We don't have the app ID yet, so we pass empty string
        tools = await mcp_client.discover_tools(
            app_data.mcp_endpoint,
            encrypted_key,
            app_id="",
            app_name=app_data.name
        )
        if tools:
            capabilities["tools"] = [asdict(t) for t in tools]
    
    # Create app
    app = MarketplaceApp(
        name=sanitize_input(app_data.name),
        slug=slug,
        description=sanitize_input(app_data.description) if app_data.description else None,
        short_description=sanitize_input(app_data.short_description) if app_data.short_description else None,
        developer_id=user.id,
        mcp_endpoint=app_data.mcp_endpoint,
        mcp_api_key_encrypted=encrypted_key,
        category=app_data.category,
        capabilities=capabilities,
        icon_url=app_data.icon_url,
        documentation_url=app_data.documentation_url,
        support_email=app_data.support_email,
        privacy_policy_url=app_data.privacy_policy_url,
        permissions={"scopes": app_data.permissions} if app_data.permissions else None,
        is_public=False,  # Starts as private until approved
        status=AppStatus.PENDING,
    )
    db.add(app)
    await db.flush()  # Flush to generate app.id before creating version
    
    # Create initial version
    version = AppVersion(
        app_id=app.id,
        version="1.0.0",
        mcp_endpoint=app_data.mcp_endpoint,
        changelog="Initial release",
    )
    db.add(version)
    
    # Audit log
    audit = AuditLog(
        user_id=user.id,
        app_id=app.id,
        action=AuditAction.APP_CREATED,
        ip_address=get_client_ip(request),
        details={"name": app.name, "slug": app.slug}
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(app)
    
    return app


@router.get("/apps/{app_id}", response_model=AppDetailResponse)
async def get_my_app(
    app_id: str,
    user: User = Depends(require_developer),
    db: AsyncSession = Depends(get_db)
):
    """Get details of an app owned by current developer."""
    result = await db.execute(
        select(MarketplaceApp).where(
            MarketplaceApp.id == app_id,
            MarketplaceApp.developer_id == user.id
        )
    )
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found"
        )
    
    return AppDetailResponse.model_validate(app)


@router.put("/apps/{app_id}", response_model=AppResponse)
async def update_app(
    app_id: str,
    app_data: AppUpdate,
    request: Request,
    user: User = Depends(require_developer),
    db: AsyncSession = Depends(get_db)
):
    """Update an app owned by current developer."""
    result = await db.execute(
        select(MarketplaceApp).where(
            MarketplaceApp.id == app_id,
            MarketplaceApp.developer_id == user.id
        )
    )
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found"
        )
    
    # Update fields
    if app_data.name:
        app.name = sanitize_input(app_data.name)
    if app_data.description:
        app.description = sanitize_input(app_data.description)
    if app_data.short_description:
        app.short_description = sanitize_input(app_data.short_description)
    if app_data.mcp_endpoint:
        app.mcp_endpoint = app_data.mcp_endpoint
    if app_data.mcp_api_key:
        app.mcp_api_key_encrypted = encrypt_value(app_data.mcp_api_key)
    if app_data.category:
        app.category = app_data.category
    if app_data.icon_url is not None:
        app.icon_url = app_data.icon_url
    if app_data.documentation_url is not None:
        app.documentation_url = app_data.documentation_url
    if app_data.support_email is not None:
        app.support_email = app_data.support_email
    if app_data.privacy_policy_url is not None:
        app.privacy_policy_url = app_data.privacy_policy_url
    if app_data.permissions is not None:
        app.permissions = {"scopes": app_data.permissions}
    
    # If MCP endpoint or key changed, refresh capabilities
    if app_data.mcp_endpoint or app_data.mcp_api_key:
        key_to_use = encrypt_value(app_data.mcp_api_key) if app_data.mcp_api_key else app.mcp_api_key_encrypted
        endpoint_to_use = app_data.mcp_endpoint if app_data.mcp_endpoint else app.mcp_endpoint
        
        if endpoint_to_use:
            tools = await mcp_client.discover_tools(
                endpoint_to_use,
                key_to_use,
                app_id=app.id,
                app_name=app.name
            )
            
            # Update capabilities while preserving other keys if any
            current_caps = app.capabilities or {}
            current_caps["tools"] = [asdict(t) for t in tools]
            app.capabilities = current_caps
    
    # If version changed, create new version record
    if app_data.version and app_data.version != app.version:
        app.version = app_data.version
        version = AppVersion(
            app_id=app.id,
            version=app_data.version,
            mcp_endpoint=app.mcp_endpoint,
            changelog=f"Updated to version {app_data.version}",
        )
        db.add(version)
    
    # Audit log
    audit = AuditLog(
        user_id=user.id,
        app_id=app.id,
        action=AuditAction.APP_UPDATED,
        ip_address=get_client_ip(request),
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(app)
    
    return app


@router.delete("/apps/{app_id}")
async def delete_app(
    app_id: str,
    request: Request,
    user: User = Depends(require_developer),
    db: AsyncSession = Depends(get_db)
):
    """Delete an app owned by current developer."""
    result = await db.execute(
        select(MarketplaceApp).where(
            MarketplaceApp.id == app_id,
            MarketplaceApp.developer_id == user.id
        )
    )
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found"
        )
    
    app_name = app.name
    
    # Audit log before deletion
    audit = AuditLog(
        user_id=user.id,
        action=AuditAction.APP_DELETED,
        ip_address=get_client_ip(request),
        details={"app_name": app_name, "app_id": app_id}
    )
    db.add(audit)
    
    await db.delete(app)
    await db.commit()
    
    return {"message": f"App '{app_name}' deleted successfully"}


@router.post("/apps/{app_id}/submit-for-review")
async def submit_for_review(
    app_id: str,
    user: User = Depends(require_developer),
    db: AsyncSession = Depends(get_db)
):
    """Submit an app for review to be listed publicly."""
    result = await db.execute(
        select(MarketplaceApp).where(
            MarketplaceApp.id == app_id,
            MarketplaceApp.developer_id == user.id
        )
    )
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found"
        )
    
    if app.status == AppStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="App is already approved"
        )
    
    if app.status == AppStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="App is already pending review"
        )
    
    app.status = AppStatus.PENDING
    app.is_public = True  # Mark as intended for public listing
    
    await db.commit()
    
    return {"message": "App submitted for review"}


@router.get("/apps/{app_id}/stats")
async def get_app_stats(
    app_id: str,
    user: User = Depends(require_developer),
    db: AsyncSession = Depends(get_db)
):
    """Get usage statistics for an app."""
    result = await db.execute(
        select(MarketplaceApp).where(
            MarketplaceApp.id == app_id,
            MarketplaceApp.developer_id == user.id
        )
    )
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found"
        )
    
    # Get install count and basic stats
    return {
        "app_id": app.id,
        "name": app.name,
        "install_count": app.install_count,
        "status": app.status.value,
        "version": app.version,
        "created_at": app.created_at,
        "updated_at": app.updated_at
    }
