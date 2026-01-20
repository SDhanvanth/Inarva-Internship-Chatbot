"""
Usage statistics endpoints.
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.user import User
from app.models.app import MarketplaceApp
from app.models.audit import UsageStats
from app.schemas.common import UsageStatsResponse, UsageSummaryResponse
from app.api.deps import require_auth


router = APIRouter(prefix="/usage", tags=["Usage"])


@router.get("/summary", response_model=UsageSummaryResponse)
async def get_usage_summary(
    period_days: int = Query(30, ge=1, le=365),
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Get usage summary for current user."""
    period_start = datetime.utcnow() - timedelta(days=period_days)
    period_end = datetime.utcnow()
    
    # Get aggregated stats
    result = await db.execute(
        select(
            func.sum(UsageStats.tokens_used),
            func.sum(UsageStats.requests_count)
        )
        .where(
            UsageStats.user_id == user.id,
            UsageStats.period_start >= period_start
        )
    )
    row = result.first()
    total_tokens = row[0] or 0
    total_requests = row[1] or 0
    
    # Get stats by app
    result = await db.execute(
        select(
            UsageStats.app_id,
            MarketplaceApp.name,
            func.sum(UsageStats.tokens_used).label('tokens'),
            func.sum(UsageStats.requests_count).label('requests')
        )
        .join(MarketplaceApp, UsageStats.app_id == MarketplaceApp.id, isouter=True)
        .where(
            UsageStats.user_id == user.id,
            UsageStats.period_start >= period_start
        )
        .group_by(UsageStats.app_id, MarketplaceApp.name)
    )
    by_app = result.all()
    
    return UsageSummaryResponse(
        total_tokens=total_tokens,
        total_requests=total_requests,
        by_app=[
            UsageStatsResponse(
                tokens_used=row.tokens or 0,
                requests_count=row.requests or 0,
                period_start=period_start,
                period_end=period_end,
                app_id=row.app_id,
                app_name=row.name or "Default Chatbot"
            )
            for row in by_app
        ],
        period_start=period_start,
        period_end=period_end
    )


@router.get("/daily")
async def get_daily_usage(
    days: int = Query(7, ge=1, le=30),
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Get daily usage breakdown."""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(
            func.date(UsageStats.period_start).label('date'),
            func.sum(UsageStats.tokens_used).label('tokens'),
            func.sum(UsageStats.requests_count).label('requests')
        )
        .where(
            UsageStats.user_id == user.id,
            UsageStats.period_start >= start_date
        )
        .group_by(func.date(UsageStats.period_start))
        .order_by(func.date(UsageStats.period_start))
    )
    daily_stats = result.all()
    
    return {
        "daily": [
            {
                "date": str(row.date),
                "tokens_used": row.tokens or 0,
                "requests_count": row.requests or 0
            }
            for row in daily_stats
        ]
    }


@router.get("/limits")
async def get_rate_limits(
    user: User = Depends(require_auth)
):
    """Get current rate limit status for user."""
    from app.config import settings
    
    return {
        "limits": {
            "requests_per_minute": settings.RATE_LIMIT_USER_PER_MINUTE,
            "requests_per_hour": settings.RATE_LIMIT_USER_PER_HOUR,
            "tool_calls_per_minute": settings.RATE_LIMIT_TOOL_PER_MINUTE,
            "burst_size": settings.RATE_LIMIT_BURST_SIZE
        },
        "message": "Use response headers to check remaining limits after each request"
    }
