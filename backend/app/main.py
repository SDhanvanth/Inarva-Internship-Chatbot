"""
AI Platform - FastAPI Application Entry Point

Production-ready API server with:
- CORS configuration
- Security middleware
- Database lifecycle management
- OpenAPI documentation
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog

from app.config import settings
from app.database import init_db, close_db
from app.redis import redis_manager
from app.mcp import mcp_client
from app.mcp.server import router as inbuilt_mcp_router
from app.mcp.gemini import gemini_client
from app.api.v1.router import router as api_router
from app.middleware.security import (
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    RequestValidationMiddleware,
)


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting AI Platform", version=settings.APP_VERSION)
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        raise
    
    # Initialize Redis
    try:
        await redis_manager.connect()
        logger.info("Redis connected")
    except Exception as e:
        logger.error("Redis connection failed", error=str(e))
        # Redis is optional for basic functionality
    
    # Initialize Gemini AI client
    if settings.INBUILT_MCP_ENABLED:
        if gemini_client.configure():
            logger.info("Gemini AI client initialized")
        else:
            logger.warning("Gemini AI client not configured - inbuilt chatbot disabled")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Platform")
    
    await mcp_client.close()
    await redis_manager.disconnect()
    await close_db()
    
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Platform with Marketplace and MCP Integration",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset", "X-Response-Time"],
)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestValidationMiddleware)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed response."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Request validation failed",
            "details": errors
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc)
    )
    
    # Don't expose internal errors in production
    if settings.DEBUG:
        message = str(exc)
    else:
        message = "An internal error occurred"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": message
        }
    )


# Include API router
app.include_router(api_router)

# Include inbuilt MCP server router
app.include_router(inbuilt_mcp_router)


# Health check endpoint (public)
@app.get("/health")
async def health_check():
    """Public health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "Disabled in production",
        "api": "/api/v1"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
        log_level="debug" if settings.DEBUG else "info",
    )
