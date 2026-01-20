"""
Security middleware for headers and request validation.
"""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import SECURITY_HEADERS


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for monitoring."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Add timing header
        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        
        # Log to database (async, non-blocking)
        # This would be done via background task in production
        
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate incoming requests."""
    
    MAX_BODY_SIZE = 10 * 1024 * 1024  # 10MB
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length:
            if int(content_length) > self.MAX_BODY_SIZE:
                return Response(
                    content='{"error": "Request body too large"}',
                    status_code=413,
                    media_type="application/json"
                )
        
        # Validate content type for POST/PUT/PATCH
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")
            if content_type and not any(
                ct in content_type.lower()
                for ct in ["application/json", "multipart/form-data", "application/x-www-form-urlencoded"]
            ):
                return Response(
                    content='{"error": "Unsupported content type"}',
                    status_code=415,
                    media_type="application/json"
                )
        
        return await call_next(request)
