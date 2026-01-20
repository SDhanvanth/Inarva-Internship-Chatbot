"""
Main API router that combines all v1 endpoints.
"""
from fastapi import APIRouter

from app.api.v1 import auth, chat, marketplace, developer, admin, usage


router = APIRouter(prefix="/api/v1")

# Include all routers
router.include_router(auth.router)
router.include_router(chat.router)
router.include_router(marketplace.router)
router.include_router(developer.router)
router.include_router(admin.router)
router.include_router(usage.router)
