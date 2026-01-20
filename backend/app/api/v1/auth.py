"""
Authentication endpoints.
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import re

from app.database import get_db
from app.models.user import User, RefreshToken, UserRole
from app.models.audit import AuditLog, AuditAction
from app.schemas.user import (
    UserCreate,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
    PasswordChange,
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_token,
    sanitize_input,
)
from app.api.deps import require_auth, get_client_ip, check_rate_limit
from app.config import settings


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(check_rate_limit)
):
    """Register a new user."""
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email.lower())
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = User(
        email=user_data.email.lower(),
        password_hash=hash_password(user_data.password),
        full_name=sanitize_input(user_data.full_name) if user_data.full_name else None,
        role=UserRole.USER,
        is_active=True,
        is_verified=False,  # Require email verification in production
    )
    db.add(user)
    
    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action=AuditAction.SIGNUP,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(check_rate_limit)
):
    """Authenticate user and return tokens."""
    # Find user
    result = await db.execute(
        select(User).where(User.email == form_data.username.lower())
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Create tokens
    access_token = create_access_token(user.id, user.role.value)
    refresh_token, refresh_expires = create_refresh_token(user.id)
    
    # Store refresh token
    token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=refresh_expires,
        user_agent=request.headers.get("User-Agent"),
        ip_address=get_client_ip(request),
    )
    db.add(token_record)
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    
    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action=AuditAction.LOGIN,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    db.add(audit)
    
    await db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(check_rate_limit)
):
    """Refresh access token using refresh token."""
    token_hash = hash_token(token_data.refresh_token)
    
    # Find valid refresh token
    result = await db.execute(
        select(RefreshToken)
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None)
        )
    )
    token_record = result.scalar_one_or_none()
    
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    if token_record.is_expired:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired"
        )
    
    # Get user
    result = await db.execute(
        select(User).where(User.id == token_record.user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Revoke old refresh token (token rotation)
    token_record.revoked_at = datetime.utcnow()
    
    # Create new tokens
    access_token = create_access_token(user.id, user.role.value)
    new_refresh_token, refresh_expires = create_refresh_token(user.id)
    
    # Store new refresh token
    new_token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(new_refresh_token),
        expires_at=refresh_expires,
        user_agent=request.headers.get("User-Agent"),
        ip_address=get_client_ip(request),
    )
    db.add(new_token_record)
    
    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action=AuditAction.TOKEN_REFRESH,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    db.add(audit)
    
    await db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(
    request: Request,
    token_data: RefreshTokenRequest,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Logout and revoke refresh token."""
    token_hash = hash_token(token_data.refresh_token)
    
    # Find and revoke token
    result = await db.execute(
        select(RefreshToken)
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == user.id,
            RefreshToken.revoked_at.is_(None)
        )
    )
    token_record = result.scalar_one_or_none()
    
    if token_record:
        token_record.revoked_at = datetime.utcnow()
    
    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action=AuditAction.LOGOUT,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    db.add(audit)
    
    await db.commit()
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: User = Depends(require_auth)
):
    """Get current user information."""
    return user


@router.post("/change-password")
async def change_password(
    request: Request,
    password_data: PasswordChange,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Change user password."""
    # Verify current password
    if not verify_password(password_data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    user.password_hash = hash_password(password_data.new_password)
    
    # Revoke all refresh tokens
    result = await db.execute(
        select(RefreshToken)
        .where(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked_at.is_(None)
        )
    )
    tokens = result.scalars().all()
    for token in tokens:
        token.revoked_at = datetime.utcnow()
    
    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action=AuditAction.PASSWORD_CHANGE,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    db.add(audit)
    
    await db.commit()
    
    return {"message": "Password changed successfully"}
