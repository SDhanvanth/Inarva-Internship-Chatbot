"""
API dependencies for authentication, rate limiting, and database sessions.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as redis

from app.database import get_db
from app.redis import get_redis
from app.config import settings
from app.models.user import User, UserRole
from app.core.security import decode_access_token
from app.core.rate_limiter import RateLimiter
from app.core.rbac import RBACChecker, Permission


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current authenticated user from JWT token."""
    if not token:
        return None
    
    payload = decode_access_token(token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    return user


async def require_auth(
    user: Optional[User] = Depends(get_current_user)
) -> User:
    """Require authenticated user."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


async def require_verified(
    user: User = Depends(require_auth)
) -> User:
    """Require verified user."""
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    return user


class RequireRole:
    """Dependency for role-based access control."""
    
    def __init__(self, roles: list[UserRole]):
        self.roles = roles
    
    async def __call__(self, user: User = Depends(require_auth)) -> User:
        if user.role not in self.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user


class RequirePermission:
    """Dependency for permission-based access control."""
    
    def __init__(self, permissions: list[Permission], require_all: bool = False):
        self.checker = RBACChecker(
            required_permissions=permissions,
            require_all=require_all
        )
    
    async def __call__(self, user: User = Depends(require_auth)) -> User:
        if not self.checker.check(user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user


# Pre-defined role dependencies
require_developer = RequireRole([UserRole.DEVELOPER, UserRole.ADMIN])
require_admin = RequireRole([UserRole.ADMIN])


async def get_rate_limiter(
    redis_client: redis.Redis = Depends(get_redis)
) -> RateLimiter:
    """Get rate limiter instance."""
    return RateLimiter(redis_client)


async def check_rate_limit(
    request: Request,
    user: Optional[User] = Depends(get_current_user),
    limiter: RateLimiter = Depends(get_rate_limiter)
) -> None:
    """Check rate limits and raise 429 if exceeded."""
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Check IP-based limit
    allowed, info = await limiter.check_ip_limit(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(info["limit"]),
                "X-RateLimit-Remaining": str(info["remaining"]),
                "X-RateLimit-Reset": str(info["reset"]),
                "Retry-After": str(info["window"])
            }
        )
    
    # Check user-based limit if authenticated
    if user:
        allowed, info = await limiter.check_user_limit(user.id)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(info["window"])
                }
            )


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    # Check for forwarded header first (behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct client
    return request.client.host if request.client else "unknown"
