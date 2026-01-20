"""
Admin endpoints for system management.
"""
import sys
import time
import psutil
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import pkg_resources

from app.database import get_db
from app.redis import redis_manager
from app.models.user import User, UserRole
from app.models.app import MarketplaceApp, AppStatus
from app.models.audit import AuditLog, AuditAction, RequestLog, UsageStats
from app.schemas.user import UserResponse, UserAdminUpdate
from app.schemas.app import AppModerationRequest, AppResponse
from app.schemas.common import (
    SystemHealthResponse,
    ServerInfoResponse,
    RequestLogListResponse,
    RequestLogResponse,
)
from app.api.deps import require_admin, get_client_ip
from app.config import settings


router = APIRouter(prefix="/admin", tags=["Admin"])

# Track server start time
SERVER_START_TIME = time.time()


@router.get("/system/health", response_model=SystemHealthResponse)
async def get_system_health(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get complete system health status."""
    # Check database
    db_healthy = True
    try:
        await db.execute(select(func.now()))
    except Exception:
        db_healthy = False
    
    # Check Redis
    redis_healthy = await redis_manager.health_check()
    
    # System resources
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return SystemHealthResponse(
        status="healthy" if db_healthy and redis_healthy else "degraded",
        version=settings.APP_VERSION,
        build_time=settings.BUILD_TIME,
        uptime_seconds=time.time() - SERVER_START_TIME,
        services={
            "database": {"status": "healthy" if db_healthy else "unhealthy"},
            "redis": {"status": "healthy" if redis_healthy else "unhealthy"},
            "mcp_servers": {"status": "healthy", "count": 0}  # TODO: implement MCP health check
        },
        system={
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2)
        }
    )


@router.get("/system/info", response_model=ServerInfoResponse)
async def get_server_info(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get complete server information."""
    # Get package versions
    packages = {}
    for pkg in ['fastapi', 'sqlalchemy', 'pydantic', 'redis', 'httpx']:
        try:
            packages[pkg] = pkg_resources.get_distribution(pkg).version
        except Exception:
            packages[pkg] = "unknown"
    
    # Get stats
    user_count = await db.execute(select(func.count()).select_from(User))
    app_count = await db.execute(select(func.count()).select_from(MarketplaceApp))
    
    # Today's requests
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    request_count = await db.execute(
        select(func.count()).select_from(RequestLog)
        .where(RequestLog.created_at >= today_start)
    )
    
    return ServerInfoResponse(
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        python_version=sys.version,
        dependencies=packages,
        config={
            "rate_limits": {
                "ip_per_minute": settings.RATE_LIMIT_IP_PER_MINUTE,
                "ip_per_hour": settings.RATE_LIMIT_IP_PER_HOUR,
                "user_per_minute": settings.RATE_LIMIT_USER_PER_MINUTE,
                "user_per_hour": settings.RATE_LIMIT_USER_PER_HOUR,
            },
            "features": {
                "debug": settings.DEBUG,
                "max_input_length": settings.MAX_INPUT_LENGTH,
            }
        },
        stats={
            "total_users": user_count.scalar() or 0,
            "total_apps": app_count.scalar() or 0,
            "requests_today": request_count.scalar() or 0
        }
    )


@router.get("/logs/requests", response_model=RequestLogListResponse)
async def get_request_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    user_id: Optional[str] = None,
    path: Optional[str] = None,
    status_code: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated API request logs with filters."""
    query = select(RequestLog)
    
    if user_id:
        query = query.where(RequestLog.user_id == user_id)
    if path:
        query = query.where(RequestLog.path.ilike(f"%{path}%"))
    if status_code:
        query = query.where(RequestLog.status_code == status_code)
    if start_date:
        query = query.where(RequestLog.created_at >= start_date)
    if end_date:
        query = query.where(RequestLog.created_at <= end_date)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Paginate
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit).order_by(RequestLog.created_at.desc())
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return RequestLogListResponse(
        logs=[RequestLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        pages=(total + limit - 1) // limit
    )


# ============================================================================
# User Management
# ============================================================================

@router.get("/users", response_model=list[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all users with filters."""
    query = select(User)
    
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if search:
        query = query.where(User.email.ilike(f"%{search}%"))
    
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(User.created_at.desc())
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return [UserResponse.model_validate(u) for u in users]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get user details."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    data: UserAdminUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update user (role, status)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    if data.role is not None:
        old_role = user.role
        user.role = data.role
        
        # Audit role change
        audit = AuditLog(
            user_id=admin.id,
            action=AuditAction.ROLE_CHANGED,
            ip_address=get_client_ip(request),
            details={
                "target_user": user_id,
                "old_role": old_role.value,
                "new_role": data.role.value
            }
        )
        db.add(audit)
    
    if data.is_active is not None:
        user.is_active = data.is_active
        
        # Audit status change
        action = AuditAction.USER_ACTIVATED if data.is_active else AuditAction.USER_SUSPENDED
        audit = AuditLog(
            user_id=admin.id,
            action=action,
            ip_address=get_client_ip(request),
            details={"target_user": user_id}
        )
        db.add(audit)
    
    if data.is_verified is not None:
        user.is_verified = data.is_verified
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


# ============================================================================
# App Moderation
# ============================================================================

@router.get("/apps/pending", response_model=list[AppResponse])
async def list_pending_apps(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List apps pending approval."""
    result = await db.execute(
        select(MarketplaceApp)
        .where(MarketplaceApp.status == AppStatus.PENDING)
        .order_by(MarketplaceApp.created_at)
    )
    apps = result.scalars().all()
    return [AppResponse.model_validate(app) for app in apps]


@router.post("/apps/{app_id}/moderate", response_model=AppResponse)
async def moderate_app(
    app_id: str,
    moderation: AppModerationRequest,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Approve or reject a marketplace app."""
    result = await db.execute(
        select(MarketplaceApp).where(MarketplaceApp.id == app_id)
    )
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found"
        )
    
    # Update status
    app.status = moderation.status
    app.reviewed_by = admin.id
    app.reviewed_at = datetime.utcnow()
    
    if moderation.status == AppStatus.REJECTED:
        app.rejection_reason = moderation.rejection_reason
        app.is_public = False
    elif moderation.status == AppStatus.APPROVED:
        app.is_public = True
    
    # Audit log
    action = AuditAction.APP_APPROVED if moderation.status == AppStatus.APPROVED else AuditAction.APP_REJECTED
    audit = AuditLog(
        user_id=admin.id,
        app_id=app.id,
        action=action,
        ip_address=get_client_ip(request),
        details={"reason": moderation.rejection_reason} if moderation.rejection_reason else None
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(app)
    
    return AppResponse.model_validate(app)


@router.get("/audit-logs")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    action: Optional[AuditAction] = None,
    user_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs."""
    query = select(AuditLog)
    
    if action:
        query = query.where(AuditLog.action == action)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
    
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit).order_by(AuditLog.created_at.desc())
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "app_id": log.app_id,
                "action": log.action.value,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at
            }
            for log in logs
        ],
        "page": page
    }
