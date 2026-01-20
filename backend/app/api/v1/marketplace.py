"""
Marketplace endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
import re

from app.database import get_db
from app.models.user import User
from app.models.app import MarketplaceApp, AppStatus, AppCategory, UserEnabledApp
from app.schemas.app import (
    AppCreate,
    AppUpdate,
    AppResponse,
    AppDetailResponse,
    AppListResponse,
    AppEnableRequest,
    EnabledAppResponse,
)
from app.api.deps import require_auth, require_developer, check_rate_limit
from app.core.security import sanitize_input, encrypt_value


router = APIRouter(prefix="/marketplace", tags=["Marketplace"])


def generate_slug(name: str) -> str:
    """Generate a URL-friendly slug from name."""
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug[:100]


@router.get("/apps", response_model=AppListResponse)
async def list_apps(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: Optional[AppCategory] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(check_rate_limit)
):
    """List public marketplace apps."""
    query = select(MarketplaceApp).where(
        MarketplaceApp.is_public == True,
        MarketplaceApp.status == AppStatus.APPROVED
    )
    
    # Apply filters
    if category:
        query = query.where(MarketplaceApp.category == category)
    
    if search:
        search_term = f"%{sanitize_input(search)}%"
        query = query.where(
            or_(
                MarketplaceApp.name.ilike(search_term),
                MarketplaceApp.description.ilike(search_term)
            )
        )
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Paginate
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(MarketplaceApp.install_count.desc())
    
    result = await db.execute(query)
    apps = result.scalars().all()
    
    return AppListResponse(
        apps=[AppResponse.model_validate(app) for app in apps],
        total=total,
        page=page,
        pages=(total + per_page - 1) // per_page,
        per_page=per_page
    )


@router.get("/apps/{app_slug}", response_model=AppDetailResponse)
async def get_app(
    app_slug: str,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(require_auth),
):
    """Get app details by slug."""
    result = await db.execute(
        select(MarketplaceApp).where(MarketplaceApp.slug == app_slug)
    )
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found"
        )
    
    # Check access
    if not app.is_public and app.status != AppStatus.APPROVED:
        if not user or (app.developer_id != user.id and user.role.value != "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    return AppDetailResponse.model_validate(app)


@router.get("/categories")
async def list_categories():
    """List available app categories."""
    return [
        {"value": cat.value, "label": cat.value.replace("_", " ").title()}
        for cat in AppCategory
    ]


# ============================================================================
# User Enabled Apps
# ============================================================================

@router.get("/my-apps", response_model=list[EnabledAppResponse])
async def list_enabled_apps(
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """List apps enabled by current user."""
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(UserEnabledApp)
        .options(selectinload(UserEnabledApp.app))
        .join(MarketplaceApp)
        .where(UserEnabledApp.user_id == user.id)
        .order_by(UserEnabledApp.enabled_at.desc())
    )
    enabled_apps = result.scalars().all()
    
    return [
        EnabledAppResponse(
            id=ea.id,
            app=AppResponse.model_validate(ea.app),
            granted_permissions=ea.granted_permissions,
            enabled_at=ea.enabled_at
        )
        for ea in enabled_apps
    ]


@router.post("/apps/{app_id}/enable", response_model=EnabledAppResponse)
async def enable_app(
    app_id: str,
    request: Optional[AppEnableRequest] = None,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Enable an app for the current user."""
    # Check if app exists and is approved
    result = await db.execute(
        select(MarketplaceApp).where(
            MarketplaceApp.id == app_id,
            MarketplaceApp.status == AppStatus.APPROVED
        )
    )
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found or not approved"
        )
    
    # Check if already enabled
    result = await db.execute(
        select(UserEnabledApp).where(
            UserEnabledApp.user_id == user.id,
            UserEnabledApp.app_id == app_id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="App already enabled"
        )
    
    # Enable app
    enabled_app = UserEnabledApp(
        user_id=user.id,
        app_id=app_id,
        granted_permissions=request.granted_permissions if request else None
    )
    db.add(enabled_app)
    
    # Update install count
    app.install_count += 1
    
    await db.commit()
    await db.refresh(enabled_app)
    
    return EnabledAppResponse(
        id=enabled_app.id,
        app=AppResponse.model_validate(app),
        granted_permissions=enabled_app.granted_permissions,
        enabled_at=enabled_app.enabled_at
    )


@router.delete("/apps/{app_id}/disable")
async def disable_app(
    app_id: str,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Disable an app for the current user."""
    result = await db.execute(
        select(UserEnabledApp).where(
            UserEnabledApp.user_id == user.id,
            UserEnabledApp.app_id == app_id
        )
    )
    enabled_app = result.scalar_one_or_none()
    
    if not enabled_app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not enabled"
        )
    
    # Get app to decrement count
    result = await db.execute(
        select(MarketplaceApp).where(MarketplaceApp.id == app_id)
    )
    app = result.scalar_one_or_none()
    if app and app.install_count > 0:
        app.install_count -= 1
    
    await db.delete(enabled_app)
    await db.commit()
    
    return {"message": "App disabled successfully"}
